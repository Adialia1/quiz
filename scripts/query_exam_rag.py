"""
Interactive Query Interface for Exam RAG System
Query exam questions by concept, topic, or similarity
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))

from rag.exam_rag import ExamRAG
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint


class ExamQueryInterface:
    """Interactive interface for querying exam questions"""

    def __init__(self):
        """Initialize the query interface"""
        self.rag = ExamRAG()
        self.console = Console()

        self.console.print(Panel.fit(
            "[bold cyan]Exam Question Query System[/bold cyan]\n"
            "Search for exam questions by concept, topic, or similarity",
            border_style="cyan"
        ))

    def search_by_concept(self, concept: str, k: int = 5) -> List[Dict]:
        """Search for questions testing a specific concept"""
        self.console.print(f"\n[bold]Searching for questions about: [cyan]{concept}[/cyan][/bold]")

        results = self.rag.find_questions_on_concept(concept, k=k)

        if not results:
            self.console.print("[red]No relevant questions found[/red]")
            return []

        return results

    def search_similar(self, query: str, k: int = 5, topic: str = None) -> List[Dict]:
        """Search for similar questions"""
        self.console.print(f"\n[bold]Searching similar to: [cyan]{query}[/cyan][/bold]")

        if topic:
            self.console.print(f"[dim]Filtered by topic: {topic}[/dim]")

        results = self.rag.search_similar_questions(query, k=k, topic=topic)

        if not results:
            self.console.print("[red]No similar questions found[/red]")
            return []

        return results

    def display_results(self, results: List[Dict], show_answers: bool = True):
        """Display search results in a formatted table"""
        if not results:
            return

        for i, q in enumerate(results, 1):
            # Create question panel
            question_text = Text(f"שאלה {i}: {q['question_text']}", style="bold")

            # Options
            options_text = Text()
            for opt in ['A', 'B', 'C', 'D', 'E']:
                opt_key = f'option_{opt.lower()}'
                if q.get(opt_key):
                    options_text.append(f"\n{opt}. {q[opt_key]}")

            # Metadata
            metadata_parts = []
            if q.get('topic'):
                metadata_parts.append(f"נושא: {q['topic']}")
            if q.get('difficulty'):
                metadata_parts.append(f"קושי: {q['difficulty']}")
            if 'similarity' in q:
                metadata_parts.append(f"דמיון: {q['similarity']:.2%}")

            metadata_text = " | ".join(metadata_parts)

            # Panel content
            panel_content = Text()
            panel_content.append(question_text)
            panel_content.append("\n")
            panel_content.append(options_text)

            if show_answers and q.get('correct_answer'):
                panel_content.append(f"\n\n[green]תשובה נכונה: {q['correct_answer']}[/green]")

            if q.get('explanation'):
                panel_content.append(f"\n[dim]הסבר: {q['explanation']}[/dim]")

            # Create panel
            panel = Panel(
                panel_content,
                title=f"[cyan]תוצאה {i}[/cyan]",
                subtitle=f"[dim]{metadata_text}[/dim]" if metadata_text else None,
                border_style="blue"
            )

            self.console.print(panel)

    def generate_exam(self, count: int = 25, topic: str = None, balanced: bool = False) -> List[Dict]:
        """Generate a random exam"""
        self.console.print(f"\n[bold]Generating exam with {count} questions[/bold]")

        if balanced:
            questions = self.rag.get_balanced_exam(count=count)
        elif topic:
            questions = self.rag.get_questions_by_topic(topic, count=count)
        else:
            questions = self.rag.get_random_exam(count=count)

        if not questions:
            self.console.print("[red]Could not generate exam - insufficient questions[/red]")
            return []

        self.console.print(f"[green]✅ Generated exam with {len(questions)} questions[/green]")

        return questions

    def export_exam(self, questions: List[Dict], output_file: str, include_answers: bool = False):
        """Export exam to file"""
        output_path = Path(output_file)

        if output_path.suffix == '.json':
            # Export as JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)

        elif output_path.suffix in ['.txt', '.md']:
            # Export as text/markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# מבחן\n\n")

                for i, q in enumerate(questions, 1):
                    f.write(f"## שאלה {i}\n")
                    f.write(f"{q['question_text']}\n\n")

                    for opt in ['A', 'B', 'C', 'D', 'E']:
                        opt_key = f'option_{opt.lower()}'
                        if q.get(opt_key):
                            f.write(f"{opt}. {q[opt_key]}\n")

                    f.write("\n---\n\n")

                if include_answers:
                    f.write("## תשובות\n\n")
                    for i, q in enumerate(questions, 1):
                        f.write(f"{i}. {q.get('correct_answer', '?')}\n")

        self.console.print(f"[green]✅ Exported to {output_path}[/green]")

    def show_statistics(self):
        """Display database statistics"""
        stats = self.rag.get_topic_statistics()
        topics = self.rag.list_topics()

        # Create table
        table = Table(title="Exam Question Database Statistics", show_header=True)
        table.add_column("Topic", style="cyan")
        table.add_column("Count", justify="right", style="magenta")

        total = 0
        for topic in sorted(topics):
            count = stats.get(topic, 0)
            table.add_row(topic or "[dim]No Topic[/dim]", str(count))
            total += count

        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

        self.console.print(table)

    def interactive_mode(self):
        """Run interactive query mode"""
        self.console.print("\n[bold cyan]Interactive Query Mode[/bold cyan]")
        self.console.print("Commands: search, exam, stats, quit")

        while True:
            try:
                command = input("\n> ").strip().lower()

                if command == 'quit' or command == 'exit':
                    break

                elif command == 'stats':
                    self.show_statistics()

                elif command.startswith('search'):
                    query = input("Enter search query: ").strip()
                    if query:
                        results = self.search_by_concept(query)
                        self.display_results(results)

                elif command.startswith('exam'):
                    count = input("Number of questions (default 25): ").strip()
                    count = int(count) if count else 25

                    topic = input("Topic (optional): ").strip()
                    topic = topic if topic else None

                    questions = self.generate_exam(count, topic)

                    if questions:
                        save = input("Save to file? (y/n): ").strip().lower()
                        if save == 'y':
                            filename = input("Filename: ").strip()
                            if filename:
                                self.export_exam(questions, filename, include_answers=True)

                elif command == 'help':
                    self.console.print("""
[bold]Available Commands:[/bold]
  search  - Search for questions by concept
  exam    - Generate a random exam
  stats   - Show database statistics
  quit    - Exit the program
                    """)

                else:
                    self.console.print(f"[red]Unknown command: {command}[/red]")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        self.console.print("\n[cyan]Goodbye![/cyan]")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Query exam questions from RAG system')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for questions')
    search_parser.add_argument('query', help='Search query (concept or question text)')
    search_parser.add_argument('-k', type=int, default=5, help='Number of results')
    search_parser.add_argument('--topic', help='Filter by topic')
    search_parser.add_argument('--no-answers', action='store_true', help='Hide correct answers')

    # Exam command
    exam_parser = subparsers.add_parser('exam', help='Generate an exam')
    exam_parser.add_argument('-n', '--count', type=int, default=25, help='Number of questions')
    exam_parser.add_argument('--topic', help='Topic for the exam')
    exam_parser.add_argument('--balanced', action='store_true', help='Balance across all topics')
    exam_parser.add_argument('-o', '--output', help='Output file (json, txt, or md)')
    exam_parser.add_argument('--with-answers', action='store_true', help='Include answers in output')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Interactive query mode')

    args = parser.parse_args()

    interface = ExamQueryInterface()

    if not args.command or args.command == 'interactive':
        interface.interactive_mode()

    elif args.command == 'search':
        results = interface.search_by_concept(args.query, k=args.k)
        interface.display_results(results, show_answers=not args.no_answers)

    elif args.command == 'exam':
        questions = interface.generate_exam(
            count=args.count,
            topic=args.topic,
            balanced=args.balanced
        )

        if questions and args.output:
            interface.export_exam(questions, args.output, include_answers=args.with_answers)
        elif questions:
            interface.display_results(questions[:5], show_answers=False)
            interface.console.print(f"\n[dim]... and {len(questions) - 5} more questions[/dim]")

    elif args.command == 'stats':
        interface.show_statistics()


if __name__ == "__main__":
    main()