import streamlit as st
import pandas as pd
from src.music_agent.prompts.prompt_manager import get_prompt_manager

st.set_page_config(page_title="Prompt Lab", page_icon="🧪", layout="wide")

st.title("🧪 Prompt Experimentation Lab")
st.caption("Test and compare different prompt variants for each agent")

pm = get_prompt_manager()

try:
    from src.music_agent.prompts import prompt_registry
except:
    st.warning("Run prompt_registry.py first to register prompts")

tab1, tab2, tab3 = st.tabs(["Test Prompts", "Compare Variants", "Metrics Dashboard"])

with tab1:
    st.header("Test Individual Prompts")
    
    if not pm.prompts:
        st.info("No prompts registered yet. Run src/music_agent/prompts/prompt_registry.py first.")
    else:
        agent_name = st.selectbox("Select Agent", list(pm.prompts.keys()))
        
        if agent_name:
            variants = pm.get_all_variants(agent_name)
            version = st.selectbox("Select Variant", list(variants.keys()))
            
            if version:
                prompt_obj = variants[version]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Prompt: {version}")
                    st.text_area("Template", prompt_obj.template, height=300, disabled=True)
                    
                    st.subheader("Test Input")
                    test_inputs = {}
                    for var in prompt_obj.variables:
                        if var == "query":
                            test_inputs[var] = st.text_input(f"{var}", "Give me energetic rock songs for workout")
                        elif var == "songs":
                            test_inputs[var] = st.text_area(f"{var}", "Song 1, Song 2, Song 3", height=100)
                        elif var == "feedback":
                            test_inputs[var] = st.text_input(f"{var}", "Make it more upbeat")
                        else:
                            test_inputs[var] = st.text_input(f"{var}", "example value")
                    
                    if st.button("Generate Prompt"):
                        try:
                            filled_prompt = prompt_obj.format(**test_inputs)
                            st.subheader("Generated Prompt")
                            st.code(filled_prompt, language="text")
                            
                            st.info(f"Estimated tokens: ~{len(filled_prompt.split()) * 1.3:.0f}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                with col2:
                    st.subheader("Metadata")
                    st.json(prompt_obj.metadata)
                    
                    st.metric("Usage Count", prompt_obj.usage_count)
                    st.metric("Success Rate", f"{prompt_obj.success_rate:.1%}")
                    st.metric("Avg Tokens", f"{prompt_obj.avg_tokens:.0f}")
                    
                    is_active = pm.active_variants.get(agent_name) == version
                    if is_active:
                        st.success("✓ Active Variant")
                    else:
                        if st.button("Set as Active"):
                            pm.set_active_variant(agent_name, version)
                            st.rerun()

with tab2:
    st.header("Compare Prompt Variants")
    
    if pm.prompts:
        compare_agent = st.selectbox("Select Agent to Compare", list(pm.prompts.keys()), key="compare_agent")
        
        if compare_agent:
            comparison = pm.compare_variants(compare_agent)
            
            if comparison:
                df = pd.DataFrame(comparison)
                
                st.subheader("Performance Comparison")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Variants", len(comparison))
                with col2:
                    best = comparison[0]
                    st.metric("Best Performer", best["version"])
                with col3:
                    active = pm.active_variants.get(compare_agent, "None")
                    st.metric("Currently Active", active)
                
                st.dataframe(
                    df[["version", "usage_count", "success_rate", "avg_tokens", "is_active"]],
                    use_container_width=True,
                    column_config={
                        "version": "Variant",
                        "usage_count": st.column_config.NumberColumn("Uses", format="%d"),
                        "success_rate": st.column_config.ProgressColumn("Success Rate", format="%.1%", min_value=0, max_value=1),
                        "avg_tokens": st.column_config.NumberColumn("Avg Tokens", format="%.0f"),
                        "is_active": st.column_config.CheckboxColumn("Active")
                    }
                )
                
                st.subheader("Side-by-Side Comparison")
                variants = pm.get_all_variants(compare_agent)
                
                cols = st.columns(min(len(variants), 3))
                for idx, (ver, prompt_obj) in enumerate(variants.items()):
                    with cols[idx % 3]:
                        st.markdown(f"**{ver}**")
                        st.caption(f"Style: {prompt_obj.metadata.get('style', 'N/A')}")
                        with st.expander("View Template"):
                            st.code(prompt_obj.template, language="text")
                        st.metric("Success", f"{prompt_obj.success_rate:.0%}")
                        st.metric("Tokens", f"{prompt_obj.avg_tokens:.0f}")

with tab3:
    st.header("Metrics Dashboard")
    
    if pm.prompts:
        st.subheader("Overall Statistics")
        
        total_agents = len(pm.prompts)
        total_variants = sum(len(variants) for variants in pm.prompts.values())
        total_usage = sum(
            prompt.usage_count 
            for variants in pm.prompts.values() 
            for prompt in variants.values()
        )
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Agents with Prompts", total_agents)
        col2.metric("Total Variants", total_variants)
        col3.metric("Total Uses", total_usage)
        
        st.subheader("Agent-wise Breakdown")
        
        agent_stats = []
        for agent_name in pm.prompts.keys():
            metrics = pm.get_metrics(agent_name)
            for version, m in metrics.items():
                agent_stats.append({
                    "Agent": agent_name,
                    "Version": version,
                    "Uses": m["usage_count"],
                    "Success Rate": m["success_rate"],
                    "Avg Tokens": m["avg_tokens"],
                    "Active": "✓" if m["is_active"] else ""
                })
        
        if agent_stats:
            df = pd.DataFrame(agent_stats)
            st.dataframe(df, use_container_width=True)
            
            st.subheader("Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(df.groupby("Agent")["Uses"].sum())
            
            with col2:
                agent_success = df.groupby("Agent")["Success Rate"].mean()
                st.bar_chart(agent_success)
    else:
        st.info("No metrics available yet. Start using the system to generate data.")

st.divider()
st.caption("💡 Tip: Test multiple variants and track their performance to find the best prompts for your use case")
