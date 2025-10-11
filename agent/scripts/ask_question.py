"""
Simple Legal Expert Query - Edit your question below
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agent.agents.legal_expert import LegalExpertAgent

# ============================================
# YOUR QUESTION HERE - Edit this line
# ============================================
question = "מה ההגדרה של 'איש פנים' לפי חוק ניירות ערך?"

# ============================================
# SETTINGS
# ============================================
# top_k = Number of legal chunks to retrieve
# 3 = Fast, basic answer
# 5 = Balanced (default)
# 10 = Thorough, for complex questions
# Max practical: 15
top_k = 5

# ============================================
# Run query
# ============================================
agent = LegalExpertAgent(top_k=top_k)
result = agent.process({"query": question})

print("\nQuestion:", question)
print("\nAnswer:")
print(result['answer'])
print("\nSources:")
for source in result['sources']:
    print(f"  - {source['document']} (עמוד {source['page']})")
