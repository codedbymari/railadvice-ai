from ai_engine import ContextualRailAdviceAI

ai = ContextualRailAdviceAI(use_manual_docs=False)

dialog = [
    "hei",
    "hvem er du?",
    "ok",
    "hade"
]

print("\n🧪 Simulert samtale:")
for msg in dialog:
    response = ai.query(msg)
    print(f"\n👤 {msg}\n🤖 {response['answer']}")

print("\n🧠 Lagret samtalekontekst:")
for entry in ai.conversation_history:
    print(f"Bruker: {entry['user']}\nAI: {entry['ai']}\n")
