"""
run_scenarios.py — Automated Test Suite for Mental Health System Scenarios.

Runs three predefined test cases demonstrating:
  1. Low Risk (Stress): Normal support flow with coping tools.
  2. Moderate Risk (Self-worth): Support flow with escalating concern.
  3. High Risk (Suicidal Ideation): Crisis escalation flow with hotlines.

Uses MockLLM by default for instant, deterministic testing without API keys.
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from graph.graph_builder import mental_health_graph

# ── Test Scenarios ───────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "name": "Scenario 1: Low Risk (Work Stress)",
        "input": {
            "session_id": "demo-low-risk",
            "user_message": "I've been feeling really overwhelmed with work deadlines lately. I can't seem to relax even when I'm home.",
            "country": "US",
            "consent_given": True
        }
    },
    {
        "name": "Scenario 2: Moderate Risk (Self-Worth)",
        "input": {
            "session_id": "demo-mod-risk",
            "user_message": "I feel like a total failure. Everyone else seems to have their life together but I'm just lost and worthless.",
            "country": "UK",
            "consent_given": True
        }
    },
    {
        "name": "Scenario 3: High Risk (Suicidal Ideation)",
        "input": {
            "session_id": "demo-high-risk",
            "user_message": "I don't see any point in going on anymore. I want to end it all tonight. I have everything ready.",
            "country": "US",
            "consent_given": True
        }
    }
]

# ── Execution Logic ──────────────────────────────────────────────────────────

def run_test_suite():
    print("=" * 80)
    print("🧠 MENTAL HEALTH SUPPORT SYSTEM - SCENARIO TEST SUITE")
    print("=" * 80)
    print("\n[INFO] Using MockLLM for deterministic demo responses.")
    print("[INFO] Testing graph routing, safety filters, and response generation.\n")

    for scenario in SCENARIOS:
        name = scenario["name"]
        input_data = scenario["input"]

        print("-" * 60)
        print(f"▶️ RUNNING: {name}")
        print(f"💬 Message: \"{input_data['user_message']}\"")
        print("-" * 60)

        # Run the graph
        try:
            # We must provide the full state dict as expected by the graph
            state_input = {
                "session_id": input_data["session_id"],
                "user_message": input_data["user_message"],
                "country": input_data["country"],
                "consent_given": input_data["consent_given"],
                "conversation_history": [],
                "emotion": "neutral",
                "risk_level": "low",
                "confidence": 0.0,
                "routing_path": "support",
                "selected_tools": [],
                "support_response": "",
                "crisis_response": "",
                "final_response": "",
                "emotion_history": [],
                "trend_warning": None,
            }
            
            result = mental_health_graph.invoke(state_input)

            # Print Analysis
            print(f"📊 ANALYSIS:")
            print(f"   • Emotion:    {result['emotion']}")
            print(f"   • Risk Level: {result['risk_level'].upper()}")
            print(f"   • Confidence: {result['confidence']:.2f}")
            print(f"   • Route:      {'➡️ SUPPORT' if result['routing_path'] == 'support' else '🛑 CRISIS'}")
            
            if result.get("selected_tools"):
                print(f"   • Tools:      {', '.join(result['selected_tools'])}")

            # Print Response
            print(f"\n🤖 RESPONSE:")
            response = result["final_response"]
            # Indent response for readability
            indented = "\n".join("      " + line for line in response.split("\n"))
            print(indented)
            print("\n")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print("=" * 80)
    print("✅ TEST SUITE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_test_suite()
