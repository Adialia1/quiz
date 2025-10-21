# Temporary file for migrating select_questions_for_exam function
# This is complex - converting Supabase ORM to raw SQL with dynamic conditions

async def select_questions_for_exam(
    question_count: int,
    topics: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    exam_type: str = "practice",
    user_id: str = None
) -> List[Dict]:
    """
    Select questions for an exam based on criteria

    Logic:
    - practice: Random questions (can repeat)
    - full_simulation: ONLY questions user has never seen before (fresh questions)
    - review_mistakes: Questions from user_mistakes table

    Adaptive Selection (when no topics specified):
    - 60-70% from user's weakest topics
    - 30-40% from all other topics (to discover new weak areas)
    """
    import random

    if exam_type == "review_mistakes" and user_id:
        # Get questions user got wrong
        results = await fetch_all(
            """
            SELECT
                um.question_id,
                q.*
            FROM user_mistakes um
            INNER JOIN ai_generated_questions q ON um.question_id = q.id
            WHERE um.user_id = $1
            AND um.is_resolved = FALSE
            LIMIT $2
            """,
            user_id, question_count
        )
        questions = results
    else:
        # Get all questions user has seen (for full_simulation filtering)
        seen_question_ids = []
        if exam_type == "full_simulation" and user_id:
            # Get all question IDs from user's history
            history = await fetch_all(
                "SELECT question_id FROM user_question_history WHERE user_id = $1",
                user_id
            )
            seen_question_ids = [item['question_id'] for item in history]

        questions = []

        # ADAPTIVE SELECTION: If no topics specified, use smart topic selection
        if not topics and user_id:
            weak_topics = await get_user_weak_topics(user_id, limit=5)

            if weak_topics:
                # 60% from weak topics, 40% from others
                weak_count = int(question_count * 0.6)
                other_count = question_count - weak_count

                # Build query for weak topics
                weak_conditions = ["is_active = TRUE"]
                weak_params = []

                # Add topic filter - using ANY for array containment
                weak_conditions.append(f"topic = ANY($1)")
                weak_params.append(weak_topics)

                if difficulty:
                    weak_conditions.append(f"difficulty_level = ${len(weak_params) + 1}")
                    weak_params.append(difficulty)

                if exam_type == "full_simulation" and seen_question_ids:
                    weak_conditions.append(f"id != ALL(${len(weak_params) + 1})")
                    weak_params.append(seen_question_ids)

                weak_conditions.append(f"LIMIT ${len(weak_params) + 1}")
                weak_params.append(weak_count * 2)

                weak_query = f"SELECT * FROM ai_generated_questions WHERE {' AND '.join(weak_conditions)}"
                weak_questions = await fetch_all(weak_query, *weak_params)

                # Build query for other topics
                other_conditions = ["is_active = TRUE"]
                other_params = []

                # Exclude weak topics
                other_conditions.append(f"topic != ALL($1)")
                other_params.append(weak_topics)

                if difficulty:
                    other_conditions.append(f"difficulty_level = ${len(other_params) + 1}")
                    other_params.append(difficulty)

                if exam_type == "full_simulation" and seen_question_ids:
                    other_conditions.append(f"id != ALL(${len(other_params) + 1})")
                    other_params.append(seen_question_ids)

                other_conditions.append(f"LIMIT ${len(other_params) + 1}")
                other_params.append(other_count * 2)

                other_query = f"SELECT * FROM ai_generated_questions WHERE {' AND '.join(other_conditions)}"
                other_questions = await fetch_all(other_query, *other_params)

                # Randomly select from each pool
                selected_weak = random.sample(weak_questions, min(weak_count, len(weak_questions)))
                selected_other = random.sample(other_questions, min(other_count, len(other_questions)))

                # Combine and shuffle
                questions = selected_weak + selected_other
                random.shuffle(questions)

        # STANDARD SELECTION: Topics specified or no adaptive selection
        if not questions:
            conditions = ["is_active = TRUE"]
            params = []

            if topics:
                conditions.append(f"topic = ANY($1)")
                params.append(topics)

            if difficulty:
                conditions.append(f"difficulty_level = ${len(params) + 1}")
                params.append(difficulty)

            # For full_simulation: exclude questions user has seen
            if exam_type == "full_simulation" and seen_question_ids:
                conditions.append(f"id != ALL(${len(params) + 1})")
                params.append(seen_question_ids)

            # Get more questions than needed for random selection
            params.append(question_count * 3)
            query = f"SELECT * FROM ai_generated_questions WHERE {' AND '.join(conditions)} LIMIT ${len(params)}"

            all_questions = await fetch_all(query, *params)

            # Randomly select question_count questions
            questions = all_questions
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)

    if len(questions) < question_count:
        if exam_type == "full_simulation" and seen_question_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough fresh questions available. You've seen {len(seen_question_ids)} questions. "
                       f"Requested: {question_count}, Fresh available: {len(questions)}. "
                       f"Try reducing question count or selecting specific topics."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough questions available. Requested: {question_count}, Available: {len(questions)}"
            )

    return questions
