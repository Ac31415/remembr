import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def load_case_studies(file_paths, case_names):
    """Load multiple evaluation_report.json files with custom names."""
    case_studies = []
    for file_path, name in zip(file_paths, case_names):
        with open(file_path, 'r') as f:
            data = json.load(f)
            case_studies.append({'name': name, 'data': data})
    return case_studies

def visualize_retrieval_navigation_performance_comparison(case_studies):
    """Creates grouped bar charts comparing retrieval and navigation performance across case studies."""
    
    # Collect all unique queries across all case studies
    all_retrieval_queries = set()
    all_navigation_queries = set()
    
    for case in case_studies:
        retrieval_data = case['data']['retrieval_performance']
        navigation_data = case['data']['navigation_performance']
        
        for q in retrieval_data['query_results']:
            all_retrieval_queries.add(q['query'])
        for q in navigation_data['query_results']:
            all_navigation_queries.add(q['query'])
    
    # Sort queries for consistent ordering
    retrieval_queries = sorted(all_retrieval_queries)
    navigation_queries = sorted(all_navigation_queries)
    
    # Create shorter labels for navigation queries (y-axis will be cluttered with long prompts)
    # Map each query to "Prompt N" where N is the index + 1
    # nav_query_labels = [f"Prompt {i+1}" for i in range(len(navigation_queries))]
    nav_query_labels = [f"{i+1}" for i in range(len(navigation_queries))][::-1]
    
    # Print query mapping for reference
    print("\n" + "="*80)
    print("NAVIGATION QUERY MAPPING:")
    print("="*80)
    for i, query in enumerate(navigation_queries):
        print(f"Prompt {i+1}: {query}")
    print("="*80 + "\n")
    
    # Prepare data for plotting
    retrieval_scores = defaultdict(list)
    retrieval_success_rates = []
    navigation_accuracy = defaultdict(list)
    navigation_success_rates = []
    case_names = []
    
    for case in case_studies:
        case_names.append(case['name'])
        retrieval_data = case['data']['retrieval_performance']
        navigation_data = case['data']['navigation_performance']
        
        # Build lookup dictionaries for this case study
        retrieval_lookup = {q['query']: q['relevance_score'] for q in retrieval_data['query_results']}
        navigation_lookup = {q['query']: q['position_accuracy'] for q in navigation_data['query_results']}
        
        # Retrieval relevance scores
        for query in retrieval_queries:
            retrieval_scores[query].append(retrieval_lookup.get(query, 0))
        
        # Retrieval success rate
        retrieval_success_rates.append(retrieval_data['success_rate'])
        
        # Navigation position accuracy
        for query in navigation_queries:
            navigation_accuracy[query].append(navigation_lookup.get(query, 0))
        
        # Navigation success rate
        navigation_success_rates.append(navigation_data['success_rate'])
    
    # Color palette for different case studies - using vibrant, distinct colors
    distinct_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    colors = [distinct_colors[i % len(distinct_colors)] for i in range(len(case_studies))]
    # bar_width = 0.8 / len(case_studies)
    bar_width = 0.4 / len(case_studies)
    
    # =========================================================================
    # FIGURE 1: Retrieval Relevance Scores
    # =========================================================================
    fig1 = plt.figure(figsize=(20, max(12, len(retrieval_queries) * 0.7)))
    ax1 = fig1.add_subplot(111)
    
    y_retrieval = np.arange(len(retrieval_queries))
    
    for i, case_name in enumerate(case_names):
        values = [retrieval_scores[query][i] for query in retrieval_queries]
        offset = (i - len(case_names)/2 + 0.5) * bar_width
        ax1.barh(y_retrieval + offset, values, bar_width, label=case_name,
                color=colors[i], alpha=0.8)
    
    ax1.set_yticks(y_retrieval)
    ax1.set_yticklabels(retrieval_queries, fontsize=22)
    ax1.set_xlabel('Relevance Score', fontsize=28)
    ax1.set_title('Retrieval Relevance Scores by Query - Case Study Comparison', fontsize=32)
    ax1.tick_params(axis='x', labelsize=24)
    ax1.legend(fontsize=18, loc='upper left', bbox_to_anchor=(1.02, 1), framealpha=0.95)
    ax1.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('retrieval_relevance_scores_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: retrieval_relevance_scores_comparison.png")
    plt.close()
    
    # =========================================================================
    # FIGURE 2: Retrieval Success Rate
    # =========================================================================
    fig2 = plt.figure(figsize=(18, 12))
    ax2 = fig2.add_subplot(111)
    
    x_success = np.arange(len(case_names))
    bars = ax2.bar(x_success, retrieval_success_rates, color=colors, alpha=0.8)
    
    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, retrieval_success_rates)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1%}',
                ha='center', va='bottom', fontsize=24, fontweight='bold')
    
    ax2.set_xticks(x_success)
    ax2.set_xticklabels(case_names, fontsize=20, rotation=15, ha='right')
    ax2.set_ylabel('Success Rate', fontsize=28)
    ax2.set_title('Retrieval Success Rate - Case Study Comparison', fontsize=32)
    ax2.tick_params(axis='y', labelsize=24)
    ax2.set_ylim([0, 1.15])
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('retrieval_success_rate_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: retrieval_success_rate_comparison.png")
    plt.close()
    
    # =========================================================================
    # FIGURE 3: Navigation Position Accuracy
    # =========================================================================
    fig3 = plt.figure(figsize=(20, max(12, len(navigation_queries) * 0.7)))
    ax3 = fig3.add_subplot(111)
    
    y_navigation = np.arange(len(navigation_queries))
    
    for i, case_name in enumerate(case_names):
        values = [navigation_accuracy[query][i] for query in navigation_queries]
        offset = (i - len(case_names)/2 + 0.5) * bar_width
        ax3.barh(y_navigation + offset, values, bar_width, label=case_name,
                color=colors[i], alpha=0.8)
    
    ax3.set_yticks(y_navigation)
    ax3.set_yticklabels(nav_query_labels, fontsize=25)  # Use shortened labels
    ax3.set_xlabel('Position Accuracy', fontsize=31)
    ax3.set_ylabel('Prompts', fontsize=31)
    # ax3.set_title('Navigation Position Accuracy by Query - Case Study Comparison', fontsize=32)
    ax3.tick_params(axis='x', labelsize=25)
    # ax3.legend(fontsize=18, loc='upper left', bbox_to_anchor=(1.02, 1), framealpha=0.95)
    ax3.grid(axis='x', alpha=0.3)
    
    # # Add note about query mapping
    # ax3.text(0.5, -0.08, 'See console output or figure comments for full query text mapping', 
    #          transform=ax3.transAxes, ha='center', fontsize=16, style='italic', color='gray')
    
    plt.tight_layout()
    plt.savefig('navigation_position_accuracy_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: navigation_position_accuracy_comparison.png")
    plt.close()
    
    # =========================================================================
    # FIGURE 4: Navigation Success Rate
    # =========================================================================
    fig4 = plt.figure(figsize=(18, 12))
    ax4 = fig4.add_subplot(111)
    
    x_nav_success = np.arange(len(case_names))
    bars = ax4.bar(x_nav_success, navigation_success_rates, color=colors, alpha=0.8)
    
    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, navigation_success_rates)):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1%}',
                ha='center', va='bottom', fontsize=24, fontweight='bold')
    
    ax4.set_xticks(x_nav_success)
    ax4.set_xticklabels(case_names, fontsize=20, rotation=15, ha='right')
    ax4.set_ylabel('Success Rate', fontsize=28)
    ax4.set_title('Navigation Success Rate - Case Study Comparison', fontsize=32)
    ax4.tick_params(axis='y', labelsize=24)
    ax4.set_ylim([0, 1.15])
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('navigation_success_rate_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: navigation_success_rate_comparison.png")
    plt.close()
    
    print("\n✅ All comparison charts saved successfully!")

# =============================================================================
# CONFIGURATION: Add your case studies here
# =============================================================================

# Define file paths and corresponding case study names
file_paths = [
    # 'evaluation_report.json',  # Example: current directory
    # Add more paths as needed, e.g.:
    '/Users/wen-chungcheng/remembr/results_20251029_051223_scream_sounds_enabled_only_memories_ACT_audio_Phi_3_vision_Command_r_RAG_full_test_standardized_queries/evaluation_report.json',
]

case_names = [
    # 'Case Study 1',  # Name for the first case study
    # Add corresponding names, e.g.:
    'VLM: Phi-3, ALM: ACT, RAG LLM: Command-R',
]

# =============================================================================
# RUN VISUALIZATION
# =============================================================================

# Load all case studies
case_studies = load_case_studies(file_paths, case_names)

# Generate comparison visualization
visualize_retrieval_navigation_performance_comparison(case_studies)