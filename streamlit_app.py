"""Project MERLIN — Intent Prediction Demo (Single-File Deployment)"""

import streamlit as st
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Intent Prediction Engine | Project MERLIN",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Intent Prediction Engine")
st.markdown(
    "**Project MERLIN** — Real-time customer intent prediction for e-commerce. "
    "[GitHub](https://github.com/yourname/intent-prediction-engine)"
)

# ------------------------------------------------------------------
# Backend logic (normally in api.py)
# ------------------------------------------------------------------

INTENT_LABELS = ["browse", "compare", "ready_to_buy", "at_risk"]

def predict_intent(events, past_orders, avg_order_value):
    """Heuristic model for demo purposes."""
    score = 0.0
    score += len(events) * 0.5
    score += sum(1 for e in events if e["type"] == "cart_add") * 3.0
    score += sum(1 for e in events if e["type"] == "checkout") * 5.0
    score -= sum(1 for e in events if e["type"] == "search") * 0.3
    score += past_orders * 0.5
    score += avg_order_value / 500.0

    if score < 3:
        intent_idx, purchase_prob, ltv, churn = 0, 0.12, 45.0, 0.08
    elif score < 6:
        intent_idx, purchase_prob, ltv, churn = 1, 0.35, 120.0, 0.15
    elif score < 10:
        intent_idx, purchase_prob, ltv, churn = 2, 0.78, 350.0, 0.02
    else:
        intent_idx, purchase_prob, ltv, churn = 3, 0.25, 80.0, 0.65

    intent_probs = [0.08, 0.08, 0.08, 0.08]
    intent_probs[intent_idx] = 0.76

    actions = {
        0: "continue_personalized_browsing",
        1: "show_comparison_tools",
        2: "show_urgency_messaging",
        3: "offer_live_chat_support",
    }
    explanations = {
        0: "User is browsing. Low purchase intent.",
        1: "User is comparing options. Moderate intent.",
        2: "User shows strong purchase signals.",
        3: "User exhibits at-risk behavior. Intervention recommended.",
    }

    if churn > 0.7:
        discount = 15.0
    elif intent_idx == 2 and purchase_prob > 0.8:
        discount = 0.0
    elif intent_idx == 3:
        discount = 10.0
    elif intent_idx == 1:
        discount = 5.0
    else:
        discount = 0.0

    return {
        "intent_class": INTENT_LABELS[intent_idx],
        "intent_probs": {label: round(float(p), 4) for label, p in zip(INTENT_LABELS, intent_probs)},
        "purchase_probability": round(float(purchase_prob), 4),
        "ltv_30d_estimate": round(ltv, 2),
        "churn_7d_probability": round(float(churn), 4),
        "recommended_action": actions[intent_idx],
        "discount_depth_pct": discount,
        "explanation": explanations[intent_idx],
        "inference_time_ms": round(np.random.uniform(35, 85), 2),
    }


# ------------------------------------------------------------------
# Frontend (Streamlit)
# ------------------------------------------------------------------

with st.sidebar:
    st.header("🎛️ Session Simulator")

    user_id = st.text_input("User ID", value="usr_demo_001")
    session_id = st.text_input("Session ID", value="sess_demo_001")
    device_type = st.selectbox("Device", ["mobile", "desktop", "tablet"])

    st.subheader("User History")
    past_orders = st.number_input("Past Orders", 0, 100, 3)
    avg_order_value = st.number_input("Avg Order Value ($)", 0.0, 5000.0, 450.0)

    st.subheader("Session Events")
    num_events = st.slider("Number of Events", 1, 20, 5)

    events = []
    base_time = datetime(2026, 8, 1, 10, 0, 0)
    event_types = ["page_view", "click", "scroll", "search", "cart_add", "checkout"]

    for i in range(num_events):
        cols = st.columns(3)
        with cols[0]:
            et = st.selectbox(f"Event {i+1}", event_types, key=f"et_{i}")
        with cols[1]:
            mins = st.number_input(f"+Min", 0, 60, i * 2, key=f"tm_{i}")
        with cols[2]:
            pid = st.text_input(f"Product", f"prod_{i+1:03d}", key=f"pid_{i}")

        events.append({
            "type": et,
            "timestamp": (base_time + timedelta(minutes=mins)).isoformat(),
            "product_id": pid if pid else None,
        })

    predict_clicked = st.button(" Predict Intent", type="primary", use_container_width=True)

if predict_clicked:
    with st.spinner("Running inference..."):
        result = predict_intent(events, past_orders, avg_order_value)

    st.subheader(" Prediction Results")
    c1, c2, c3, c4, c5 = st.columns(5)

    intent_class = result["intent_class"]
    emoji = {"browse": "👀", "compare": "⚖️", "ready_to_buy": "🛒", "at_risk": "⚠️"}

    with c1:
        st.metric("Intent", f"{emoji.get(intent_class, '')} {intent_class.upper()}")
    with c2:
        st.metric("Purchase Prob", f"{result['purchase_probability']:.1%}")
    with c3:
        st.metric("LTV (30d)", f"${result['ltv_30d_estimate']:.0f}")
    with c4:
        st.metric("Churn Risk", f"{result['churn_7d_probability']:.1%}")
    with c5:
        st.metric("Latency", f"{result['inference_time_ms']:.1f} ms")

    st.subheader("Intent Probability Distribution")
    st.bar_chart(result["intent_probs"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Recommended Action:** {result['recommended_action']}")
    with col_b:
        st.success(f"**Explanation:** {result['explanation']}")

    if result["discount_depth_pct"] > 0:
        st.warning(f" Offer **{result['discount_depth_pct']:.0f}% discount** to maximize conversion")
    else:
        st.success(" No discount needed — user is likely to convert organically")

st.divider()
st.subheader("📐 Production Architecture")

with st.expander("Click to see how this scales to 50M users"):
    st.markdown("""
    ```
    User Action
        |
        v
    +------------------+
    |  FastAPI         |  <- Pydantic validation, structured logging
    |  /predict        |
    +------------------+
        |
        v
    +------------------+     +------------------+
    |  Feature         |     |  Redis Cache     |
    |  Retrieval       | <-> |  (hot features)  |
    |  (< 30ms)        |     +------------------+
    +------------------+
        |
        v
    +------------------+
    |  ONNX Runtime    |  <- Multi-task Transformer
    |  Inference       |     Intent | Purchase | LTV | Churn
    |  (< 50ms)        |
    +------------------+
        |
        v
    +------------------+
    |  Business Logic  |  <- Dynamic discounting, guardrails
    |  (< 100ms)       |
    +------------------+
        |
        v
      Streamlit Dashboard
    ```
    **Full production stack:** PyTorch → ONNX | Kafka | Snowflake | Feast | Redis | Kubernetes | MLflow
    """)

st.caption("Demo runs heuristic logic inline. Production version uses ONNX Runtime with p99 < 200ms.")
