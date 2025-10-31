#!/usr/bin/env python
"""
Script para testar processamento de português dentro do container
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from transcription.portuguese_processor import PortugueseBRTextProcessor

# Testes
test_cases = [
    "Então tipo você sabe né isso é bem importante hã",
    "O sr joão trabalha na ltda da costa",
    "O texto tem espaço errado , antes de vírgula",
    "joão mora em são paulo . ele trabalha na costa .",
    "Você pode me chamar quando chegar no escritório ok ?",
]

print("=" * 70)
print("🇧🇷 TESTE DE PROCESSAMENTO DE PORTUGUÊS BRASILEIRO")
print("=" * 70)

for i, text in enumerate(test_cases, 1):
    processed = PortugueseBRTextProcessor.process(text)
    print(f"\n{i}. Teste:")
    print(f"   Entrada: {text}")
    print(f"   Saída:   {processed}")

print("\n" + "=" * 70)
print("✅ Teste concluído com sucesso!")
print("=" * 70)
