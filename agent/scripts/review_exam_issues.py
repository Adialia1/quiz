"""
Interactive Review Tool for Problematic Exam Questions
Helps identify and fix mismatches between questions, options, and answers
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent))

from agent.ingestion.llm_exam_parser import LLMExamParser
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint


class ExamReviewTool:
    """Interactive tool for reviewing and fixing exam question issues"""

    def __init__(self):
        self.console = Console()
        self.parser = LLMExamParser()

    def review_pdf(self, pdf_path: str):
        """Review an exam PDF and identify issues"""
        self.console.print(Panel.fit(
            f"[bold cyan]Reviewing Exam PDF[/bold cyan]\n{pdf_path}",
            border_style="cyan"
        ))

        # Extract with validation
        valid_questions, report = self.parser.extract_and_validate(
            pdf_path,
            use_llm_validation=True
        )

        # Display report
        self._display_validation_report(report)

        # Show problematic questions
        if report.get('llm_issues'):
            self.console.print(f"\n[bold red]⚠️  Found {len(report['llm_issues'])} problematic questions[/bold red]")

            review = Confirm.ask("Review problematic questions?")
            if review:
                self._review_issues(report['llm_issues'], valid_questions)

        # Show questions with low confidence
        low_confidence = [
            q for q in valid_questions
            if q.get('validation', {}).get('confidence', 1.0) < 0.8
        ]

        if low_confidence:
            self.console.print(f"\n[yellow]⚠️  {len(low_confidence)} questions have low confidence[/yellow]")
            review = Confirm.ask("Review low-confidence questions?")
            if review:
                self._review_low_confidence(low_confidence)

        # Summary
        self.console.print(f"\n[bold green]✅ Final: {len(valid_questions)} valid questions[/bold green]")

        # Export option
        if valid_questions:
            export = Confirm.ask("Export valid questions to JSON?")
            if export:
                output_path = Prompt.ask("Output file path", default="validated_questions.json")
                self._export_questions(valid_questions, output_path)

    def _display_validation_report(self, report: Dict):
        """Display validation report in a table"""
        table = Table(title="Validation Report", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        table.add_column("Rate", justify="right", style="green")

        total = report.get('total_extracted', 0)
        basic_valid = report.get('basic_valid', 0)
        llm_valid = report.get('llm_valid', 0)
        llm_rejected = report.get('llm_rejected', 0)

        table.add_row(
            "Total Extracted",
            str(total),
            "100%"
        )

        if total > 0:
            table.add_row(
                "Basic Valid",
                str(basic_valid),
                f"{(basic_valid/total)*100:.1f}%"
            )

            table.add_row(
                "LLM Validated",
                str(llm_valid),
                f"{(llm_valid/total)*100:.1f}%"
            )

            if llm_rejected > 0:
                table.add_row(
                    "[red]LLM Rejected[/red]",
                    f"[red]{llm_rejected}[/red]",
                    f"[red]{(llm_rejected/total)*100:.1f}%[/red]"
                )

        self.console.print(table)

    def _review_issues(self, issues: List[Dict], all_questions: List[Dict]):
        """Interactively review problematic questions"""
        for i, issue in enumerate(issues, 1):
            self.console.print(f"\n[bold]Issue {i}/{len(issues)}[/bold]")

            # Find the full question
            q_num = issue.get('question_number')
            full_question = next((q for q in all_questions if q.get('question_number') == q_num), None)

            if full_question:
                self._display_question_with_issues(full_question, issue)

                # Check if auto-fix is available
                validation = full_question.get('validation', {})
                has_fix = validation.get('context_search', {}).get('found_better_context', False)
            else:
                self.console.print(issue)
                has_fix = False

            # Options
            if has_fix:
                self.console.print("\n[dim]Options: [f]ix auto, [s]kip, [e]dit manual, [d]elete, [q]uit[/dim]")
                action = Prompt.ask("Action", choices=['f', 's', 'e', 'd', 'q'], default='f')
            else:
                self.console.print("\n[dim]Options: [s]kip, [e]dit, [d]elete, [q]uit[/dim]")
                action = Prompt.ask("Action", choices=['s', 'e', 'd', 'q'], default='s')

            if action == 'q':
                break
            elif action == 'f' and has_fix and full_question:
                self._apply_auto_fix(full_question)
            elif action == 'e' and full_question:
                self._edit_question(full_question)
            elif action == 'd' and full_question:
                self.console.print("[red]Question marked for deletion[/red]")
                full_question['_delete'] = True
            elif not full_question:
                self.console.print("[red]Question not found in validated list[/red]")

    def _review_low_confidence(self, questions: List[Dict]):
        """Review questions with low confidence scores"""
        for i, question in enumerate(questions, 1):
            confidence = question.get('validation', {}).get('confidence', 0)
            issues = question.get('validation', {}).get('issues', [])

            self.console.print(f"\n[bold]Question {i}/{len(questions)} (Confidence: {confidence:.1%})[/bold]")

            self._display_question(question)

            if issues:
                self.console.print(f"\n[yellow]Issues detected:[/yellow]")
                for issue in issues:
                    self.console.print(f"  • {issue}")

            # Options
            action = Prompt.ask("Action", choices=['s', 'e', 'd', 'q'], default='s')

            if action == 'q':
                break
            elif action == 'e':
                self._edit_question(question)
            elif action == 'd':
                question['_delete'] = True

    def _display_question(self, question: Dict):
        """Display a question in a formatted panel"""
        # Build question text
        text = f"[bold]שאלה {question.get('question_number')}:[/bold]\n"
        text += f"{question.get('question_text', '')}\n\n"

        # Options
        options = question.get('options', {})
        for opt in ['A', 'B', 'C', 'D', 'E']:
            if opt in options:
                text += f"[cyan]{opt}.[/cyan] {options[opt]}\n"

        # Correct answer
        correct = question.get('correct_answer', '?')
        text += f"\n[green]תשובה נכונה: {correct}[/green]"

        # Validation info
        validation = question.get('validation', {})
        if validation:
            conf = validation.get('confidence', 0)
            text += f"\n[dim]Confidence: {conf:.1%}[/dim]"

        panel = Panel(text, border_style="blue")
        self.console.print(panel)

    def _display_question_with_issues(self, question: Dict, issue: Dict):
        """Display question with highlighted issues"""
        self._display_question(question)

        # Show issues
        if issue.get('issues'):
            self.console.print(f"\n[red]⚠️  Issues:[/red]")
            for i in issue['issues']:
                self.console.print(f"  [red]•[/red] {i}")

        # Show confidence
        confidence = issue.get('confidence', 0)
        self.console.print(f"\n[yellow]Confidence: {confidence:.1%}[/yellow]")

        # Show suggested fix if available (from context search)
        validation = question.get('validation', {})
        context_search = validation.get('context_search', {})

        if context_search.get('found_better_context'):
            self.console.print(f"\n[bold green]✨ Found Correct Options![/bold green]")

            original_page = context_search.get('original_page')
            found_page = context_search.get('found_on_page')

            self.console.print(f"[dim]Searched pages {original_page-1} to {original_page+1}[/dim]")
            self.console.print(f"[green]Found on page: {found_page}[/green]")

            corrected = context_search.get('corrected_question', {})

            if corrected.get('options'):
                self.console.print(f"\n[bold cyan]Corrected Options:[/bold cyan]")
                for opt, text in corrected['options'].items():
                    self.console.print(f"  {opt}. {text}")

                if corrected.get('correct_answer'):
                    self.console.print(f"\n[green]Correct Answer: {corrected['correct_answer']}[/green]")

                # Offer to auto-fix
                self.console.print(f"\n[bold]Auto-fix available! Press 'f' to apply fix.[/bold]")

    def _apply_auto_fix(self, question: Dict):
        """Apply auto-fix from context search"""
        validation = question.get('validation', {})
        context_search = validation.get('context_search', {})
        corrected = context_search.get('corrected_question', {})

        if corrected:
            # Update question with corrected data
            if corrected.get('options'):
                question['options'] = corrected['options']

            if corrected.get('correct_answer'):
                question['correct_answer'] = corrected['correct_answer']

            question['_auto_fixed'] = True
            question['_original_page'] = context_search.get('original_page')
            question['_found_on_page'] = context_search.get('found_on_page')

            self.console.print("[bold green]✅ Auto-fix applied![/bold green]")
            self.console.print(f"[dim]Options corrected from page {question['_found_on_page']}[/dim]")

    def _edit_question(self, question: Dict):
        """Interactive question editor"""
        self.console.print("\n[bold cyan]Edit Question[/bold cyan]")

        # Edit question text
        current_q = question.get('question_text', '')
        new_q = Prompt.ask("Question text", default=current_q)
        if new_q != current_q:
            question['question_text'] = new_q

        # Edit options
        options = question.get('options', {})
        for opt in ['A', 'B', 'C', 'D', 'E']:
            current = options.get(opt, '')
            new_opt = Prompt.ask(f"Option {opt}", default=current)
            if new_opt != current:
                options[opt] = new_opt

        # Edit correct answer
        current_answer = question.get('correct_answer', '')
        new_answer = Prompt.ask("Correct answer", choices=['A', 'B', 'C', 'D', 'E'], default=current_answer)
        if new_answer != current_answer:
            question['correct_answer'] = new_answer

        question['_edited'] = True
        self.console.print("[green]✅ Question updated[/green]")

    def _export_questions(self, questions: List[Dict], output_path: str):
        """Export questions to JSON file"""
        # Remove questions marked for deletion
        to_export = [q for q in questions if not q.get('_delete')]

        # Clean up internal fields
        for q in to_export:
            q.pop('_delete', None)
            q.pop('_edited', None)
            q.pop('raw_text', None)
            q.pop('validation', None)

        # Convert to standard format
        export_data = []
        for q in to_export:
            export_data.append({
                'question': q.get('question_text'),
                'options': q.get('options'),
                'correct_answer': q.get('correct_answer'),
                'page_number': q.get('page_number'),
                'question_number': q.get('question_number')
            })

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]✅ Exported {len(export_data)} questions to {output_path}[/green]")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Review exam questions for issues')
    parser.add_argument('pdf_path', help='Path to exam PDF')

    args = parser.parse_args()

    tool = ExamReviewTool()
    tool.review_pdf(args.pdf_path)


if __name__ == "__main__":
    main()
