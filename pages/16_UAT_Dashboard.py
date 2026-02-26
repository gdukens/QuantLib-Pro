"""
UAT Dashboard - User Acceptance Testing Portal

Streamlit page for UAT management, feedback collection, bug tracking, and reporting.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

from quantlib_pro.uat import (
    UATScenarioLibrary,
    UATExecutor,
    FeedbackCollector,
    FeedbackAnalyzer,
    BugTracker,
    PerformanceValidator,
    FeedbackType,
    Severity,
    FeedbackStatus,
    TestStatus,
    UserRole,
    Priority,
)


# Page config
st.set_page_config(
    page_title="UAT Dashboard",
    page_icon="",
    layout="wide"
)

st.title("User Acceptance Testing Dashboard")
st.markdown("*Comprehensive UAT management, feedback collection, and quality assurance*")

# Initialize components
@st.cache_resource
def init_uat_components():
    """Initialize UAT components."""
    executor = UATExecutor()
    executor.load_scenarios(UATScenarioLibrary.get_all_scenarios())
    
    feedback_collector = FeedbackCollector()
    feedback_analyzer = FeedbackAnalyzer(feedback_collector)
    
    bug_tracker = BugTracker()
    
    performance_validator = PerformanceValidator()
    
    return executor, feedback_collector, feedback_analyzer, bug_tracker, performance_validator


executor, feedback_collector, feedback_analyzer, bug_tracker, performance_validator = init_uat_components()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " UAT Scenarios",
    " Feedback",
    " Bug Tracking",
    " Performance",
    " Reports",
    " Metrics"
])

# ============================================================================
# TAB 1: UAT Scenarios
# ============================================================================
with tab1:
    st.header("UAT Test Scenarios")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Filters")
        
        # Role filter
        role_filter = st.selectbox(
            "Filter by Role",
            ["All"] + [role.value for role in UserRole]
        )
        
        # Priority filter
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All"] + [priority.value for priority in Priority]
        )
        
        # Status filter
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + [status.value for status in TestStatus]
        )
    
    with col2:
        st.subheader("Scenarios")
        
        # Filter scenarios
        scenarios = executor.scenarios.copy()
        
        if role_filter != "All":
            scenarios = [s for s in scenarios if s.user_role.value == role_filter]
        if priority_filter != "All":
            scenarios = [s for s in scenarios if s.priority.value == priority_filter]
        if status_filter != "All":
            scenarios = [s for s in scenarios if s.status.value == status_filter]
        
        # Display scenarios
        for scenario in scenarios:
            with st.expander(f"{scenario.scenario_id}: {scenario.title} [{scenario.status.value.upper()}]"):
                st.markdown(f"**Description:** {scenario.description}")
                st.markdown(f"**User Role:** {scenario.user_role.value}")
                st.markdown(f"**Priority:** {scenario.priority.value}")
                st.markdown(f"**Status:** {scenario.status.value}")
                
                if scenario.prerequisites:
                    st.markdown("**Prerequisites:**")
                    for prereq in scenario.prerequisites:
                        st.markdown(f"- {prereq}")
                
                st.markdown("**Test Steps:**")
                for step in scenario.steps:
                    status_icon = "" if step.passed is True else "" if step.passed is False else ""
                    st.markdown(f"{status_icon} **Step {step.step_number}:** {step.description}")
                    st.markdown(f"   *Expected:* {step.expected_result}")
                
                if scenario.completion_percentage > 0:
                    st.progress(scenario.completion_percentage / 100)
                    st.caption(f"Completion: {scenario.completion_percentage:.1f}%")
    
    # Summary statistics
    st.subheader("UAT Progress")
    
    summary = executor.get_summary()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Scenarios", summary.get('total_scenarios', 0))
    with col2:
        st.metric("Passed", summary.get('passed', 0))
    with col3:
        st.metric("Failed", summary.get('failed', 0))
    with col4:
        st.metric("In Progress", summary.get('in_progress', 0))
    with col5:
        st.metric("Pass Rate", f"{summary.get('pass_rate', 0):.1f}%")

# ============================================================================
# TAB 2: Feedback Collection
# ============================================================================
with tab2:
    st.header("Feedback Collection")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Submit Feedback")
        
        with st.form("feedback_form"):
            user_name = st.text_input("Your Name", key="fb_name")
            user_role = st.selectbox(
                "Your Role",
                [role.value for role in UserRole],
                key="fb_role"
            )
            
            feedback_type = st.selectbox(
                "Feedback Type",
                [ft.value for ft in FeedbackType],
                key="fb_type"
            )
            
            severity = st.selectbox(
                "Severity",
                [s.value for s in Severity],
                key="fb_severity"
            )
            
            title = st.text_input("Title", key="fb_title")
            description = st.text_area("Description", key="fb_description", height=150)
            
            page = st.text_input("Page/Feature", key="fb_page")
            
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                if user_name and title and description:
                    feedback = feedback_collector.submit_feedback(
                        user_name=user_name,
                        user_role=user_role,
                        feedback_type=FeedbackType(feedback_type),
                        severity=Severity(severity),
                        title=title,
                        description=description,
                        page=page
                    )
                    st.success(f" Feedback submitted! ID: {feedback.feedback_id}")
                else:
                    st.error("Please fill in all required fields")
    
    with col2:
        st.subheader("Recent Feedback")
        
        # Get statistics
        stats = feedback_collector.get_statistics()
        
        if stats.get('total', 0) > 0:
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Feedback", stats['total'])
            with col2:
                st.metric("Open Critical", stats.get('open_critical', 0))
            with col3:
                st.metric("Open High", stats.get('open_high', 0))
            with col4:
                st.metric("Resolution Rate", f"{stats.get('resolution_rate', 0):.1f}%")
            
            # Recent feedback list
            feedback_items = feedback_collector.feedback_items[-10:]  # Last 10
            feedback_items.reverse()
            
            for feedback in feedback_items:
                severity_color = {
                    'critical': '',
                    'high': '',
                    'medium': '',
                    'low': ''
                }.get(feedback.severity.value, '')
                
                with st.expander(
                    f"{severity_color} {feedback.feedback_id}: {feedback.title} "
                    f"[{feedback.status.value}]"
                ):
                    st.markdown(f"**Type:** {feedback.feedback_type.value}")
                    st.markdown(f"**Severity:** {feedback.severity.value}")
                    st.markdown(f"**Submitted by:** {feedback.user_name} ({feedback.user_role})")
                    st.markdown(f"**Date:** {feedback.timestamp.strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(f"**Page:** {feedback.page or 'N/A'}")
                    st.markdown(f"**Description:** {feedback.description}")
                    
                    if feedback.assignee:
                        st.markdown(f"**Assigned to:** {feedback.assignee}")
                    if feedback.resolution:
                        st.markdown(f"**Resolution:** {feedback.resolution}")
        else:
            st.info("No feedback submitted yet. Be the first to provide feedback!")

# ============================================================================
# TAB 3: Bug Tracking
# ============================================================================
with tab3:
    st.header("Bug Tracking")
    
    metrics = bug_tracker.get_bug_metrics()
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Bugs", metrics.get('total', 0))
    with col2:
        st.metric("Open", metrics.get('open', 0))
    with col3:
        st.metric("Resolved", metrics.get('resolved', 0))
    with col4:
        st.metric(
            "Avg Resolution Time",
            f"{metrics.get('avg_resolution_time_hours', 0):.1f}h"
        )
    with col5:
        st.metric("Resolution Rate", f"{metrics.get('resolution_rate', 0):.1f}%")
    
    st.subheader("Critical Bugs")
    
    critical_bugs = bug_tracker.get_critical_bugs()
    
    if critical_bugs:
        for bug in critical_bugs:
            with st.expander(
                f" {bug.bug_id}: {bug.title} [{bug.priority.value.upper()}]"
            ):
                st.markdown(f"**Category:** {bug.category.value}")
                st.markdown(f"**Severity:** {bug.severity.value}")
                st.markdown(f"**Status:** {bug.status.value}")
                st.markdown(f"**Reporter:** {bug.reporter}")
                st.markdown(f"**Reported:** {bug.reported_date.strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Page:** {bug.page}")
                
                st.markdown("**Steps to Reproduce:**")
                for i, step in enumerate(bug.steps_to_reproduce, 1):
                    st.markdown(f"{i}. {step}")
                
                st.markdown(f"**Expected:** {bug.expected_behavior}")
                st.markdown(f"**Actual:** {bug.actual_behavior}")
                
                if bug.assignee:
                    st.markdown(f"**Assigned to:** {bug.assignee}")
                if bug.resolution:
                    st.markdown(f"**Resolution:** {bug.resolution}")
    else:
        st.success(" No critical bugs! Great work!")
    
    st.subheader("Bug Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # By priority
        if metrics.get('by_priority'):
            priority_data = []
            for priority, counts in metrics['by_priority'].items():
                priority_data.append({
                    'Priority': priority,
                    'Open': counts['open'],
                    'Resolved': counts['resolved']
                })
            
            df_priority = pd.DataFrame(priority_data)
            
            fig_priority = px.bar(
                df_priority,
                x='Priority',
                y=['Open', 'Resolved'],
                title="Bugs by Priority",
                barmode='group'
            )
            st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        # By category
        if metrics.get('by_category'):
            category_data = pd.DataFrame([
                {'Category': cat, 'Count': count}
                for cat, count in metrics['by_category'].items()
            ])
            
            fig_category = px.pie(
                category_data,
                values='Count',
                names='Category',
                title="Bugs by Category"
            )
            st.plotly_chart(fig_category, use_container_width=True)

# ============================================================================
# TAB 4: Performance Validation
# ============================================================================
with tab4:
    st.header("Performance Validation")
    
    st.markdown("""
    Automated performance validation to ensure system meets performance requirements.
    Each benchmark runs multiple times to get accurate performance statistics.
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Run Benchmarks")
        
        category = st.selectbox(
            "Category",
            ["All", "portfolio", "risk", "options", "regime", "backtest"]
        )
        
        executions = st.slider("Executions per benchmark", 1, 20, 10)
        
        if st.button("Run Performance Tests", type="primary"):
            with st.spinner("Running performance benchmarks..."):
                if category == "All":
                    results = performance_validator.run_all_benchmarks(executions=executions)
                else:
                    results = performance_validator.run_all_benchmarks(
                        category=category,
                        executions=executions
                    )
                st.success(f" Completed {len(results)} benchmarks")
    
    with col2:
        st.subheader("Results")
        
        summary = performance_validator.get_summary()
        
        if summary.get('total', 0) > 0:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tests", summary['total'])
            with col2:
                st.metric("Passed", summary['passed'])
            with col3:
                st.metric("Failed", summary['failed'])
            with col4:
                st.metric("Pass Rate", f"{summary.get('pass_rate', 0):.1f}%")
            
            # Results table
            results_data = []
            for result in performance_validator.results:
                results_data.append({
                    'Benchmark': result.benchmark_name,
                    'Status': result.status.value,
                    'Mean (ms)': f"{result.mean_ms:.2f}",
                    'P95 (ms)': f"{result.p95_ms:.2f}",
                    'Baseline (ms)': f"{result.baseline_ms:.2f}",
                    'Regression %': f"{result.regression_pct:.1f}%",
                })
            
            df_results = pd.DataFrame(results_data)
            st.dataframe(df_results, use_container_width=True)
            
            # Regressions
            regressions = performance_validator.get_regressions()
            if regressions:
                st.warning(f" {len(regressions)} performance regressions detected!")
                for reg in regressions:
                    st.markdown(
                        f"- **{reg.benchmark_name}**: {reg.regression_pct:.1f}% slower "
                        f"({reg.mean_ms:.2f}ms vs baseline {reg.baseline_ms:.2f}ms)"
                    )
        else:
            st.info("No performance tests run yet. Click 'Run Performance Tests' to start.")

# ============================================================================
# TAB 5: Reports
# ============================================================================
with tab5:
    st.header("UAT Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Feedback Report")
        
        report = feedback_collector.generate_report()
        
        st.json(report['statistics'])
        
        if st.button("Export Feedback CSV"):
            feedback_collector.export_csv("data/uat/feedback_export.csv")
            st.success(" Exported to data/uat/feedback_export.csv")
    
    with col2:
        st.subheader("Bug Report")
        
        if st.button("Export Bug Report"):
            bug_tracker.export_bug_report("data/uat/bug_report.json")
            st.success(" Exported to data/uat/bug_report.json")
        
        if st.button("Export Performance Report"):
            performance_validator.export_report("data/uat/performance_report.json")
            st.success(" Exported to data/uat/performance_report.json")

# ============================================================================
# TAB 6: Overall Metrics
# ============================================================================
with tab6:
    st.header("UAT Metrics Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Test Execution")
        
        uat_summary = executor.get_summary()
        
        if uat_summary.get('total_scenarios', 0) > 0:
            # Pie chart of test status
            status_data = pd.DataFrame([
                {'Status': 'Passed', 'Count': uat_summary.get('passed', 0)},
                {'Status': 'Failed', 'Count': uat_summary.get('failed', 0)},
                {'Status': 'In Progress', 'Count': uat_summary.get('in_progress', 0)},
                {'Status': 'Not Started', 'Count': uat_summary.get('not_started', 0)},
            ])
            
            fig_status = px.pie(
                status_data,
                values='Count',
                names='Status',
                title="Test Execution Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("Feedback Status")
        
        fb_stats = feedback_collector.get_statistics()
        
        if fb_stats.get('total', 0) > 0:
            # By type
            type_data = pd.DataFrame([
                {'Type': type_name, 'Count': count}
                for type_name, count in fb_stats.get('by_type', {}).items()
            ])
            
            fig_type = px.bar(
                type_data,
                x='Type',
                y='Count',
                title="Feedback by Type"
            )
            st.plotly_chart(fig_type, use_container_width=True)
    
    with col3:
        st.subheader("Quality Metrics")
        
        bug_metrics = bug_tracker.get_bug_metrics()
        
        # Quality score
        total_tests = uat_summary.get('total_scenarios', 0)
        passed_tests = uat_summary.get('passed', 0)
        total_bugs = bug_metrics.get('total', 0)
        open_critical = len(bug_tracker.get_critical_bugs())
        
        quality_score = 0
        if total_tests > 0:
            test_score = (passed_tests / total_tests) * 40
            bug_score = max(0, 30 - total_bugs * 2)
            critical_score = max(0, 30 - open_critical * 10)
            quality_score = test_score + bug_score + critical_score
        
        st.metric("Quality Score", f"{quality_score:.0f}/100")
        
        st.progress(quality_score / 100)
        
        if quality_score >= 90:
            st.success(" Excellent quality!")
        elif quality_score >= 70:
            st.info(" Good quality")
        elif quality_score >= 50:
            st.warning(" Needs improvement")
        else:
            st.error(" Critical issues")
    
    # Trending issues
    st.subheader("Trending Issues")
    
    trending = feedback_collector.get_trending_issues()
    
    if trending:
        trending_df = pd.DataFrame(trending)
        st.dataframe(trending_df, use_container_width=True)
    else:
        st.info("No trending issues detected")

# Footer
st.divider()
st.caption(f"UAT Dashboard | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
