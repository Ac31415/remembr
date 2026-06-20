# import json
# import matplotlib.pyplot as plt

# def visualize_content_categories(data):
#     """Creates pie charts for visual and audio content categories."""
#     content_data = data['content_analysis']
#     visual_categories = content_data['visual_categories']
#     audio_categories = content_data['audio_categories']
    
#     fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
#     fig.suptitle('Content Category Breakdown', fontsize=24)
    
#     # Visual categories pie chart
#     ax1.pie(visual_categories.values(), labels=visual_categories.keys(), autopct='%1.1f%%', startangle=90)
#     ax1.set_title('Visual Content Categories', fontsize=16)
    
#     # Audio categories pie chart
#     ax2.pie(audio_categories.values(), labels=audio_categories.keys(), autopct='%1.1f%%', startangle=90)
#     ax2.set_title('Audio Content Categories', fontsize=16)

#     plt.tight_layout(rect=[0, 0, 1, 0.95])
#     plt.show()

# # Load the JSON data from the file
# with open('memory_analysis.json', 'r') as f:
#     memory_data = json.load(f)

# visualize_content_categories(memory_data)



















import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def load_case_studies(file_paths, case_names):
    """Load multiple memory_analysis.json files with custom names."""
    case_studies = []
    for file_path, name in zip(file_paths, case_names):
        with open(file_path, 'r') as f:
            data = json.load(f)
            case_studies.append({'name': name, 'data': data})
    return case_studies

def visualize_content_categories_comparison(case_studies):
    """Creates grouped bar charts comparing visual and audio categories across case studies."""
    
    # Collect all unique categories across all case studies
    all_visual_categories = set()
    all_audio_categories = set()
    
    for case in case_studies:
        content_data = case['data']['content_analysis']
        all_visual_categories.update(content_data['visual_categories'].keys())
        all_audio_categories.update(content_data['audio_categories'].keys())
    
    # Sort categories for consistent ordering
    visual_categories = sorted(all_visual_categories)
    audio_categories = sorted(all_audio_categories)
    
    # Prepare data for plotting
    visual_data = defaultdict(list)
    audio_data = defaultdict(list)
    case_names = []
    
    for case in case_studies:
        case_names.append(case['name'])
        content_data = case['data']['content_analysis']
        
        # Visual categories
        for cat in visual_categories:
            visual_data[cat].append(content_data['visual_categories'].get(cat, 0))
        
        # Audio categories
        for cat in audio_categories:
            audio_data[cat].append(content_data['audio_categories'].get(cat, 0))
    
    # Color palette for different case studies
    colors = plt.cm.Set3(np.linspace(0, 1, len(case_studies)))
    bar_width = 0.8 / len(case_studies)  # Adjust width based on number of case studies
    
    # =========================================================================
    # VISUAL CATEGORIES PLOT
    # =========================================================================
    fig1 = plt.figure(figsize=(20, 10))
    ax1 = fig1.add_subplot(111)
    
    x_visual = np.arange(len(visual_categories))
    
    # Plot Visual categories
    for i, case_name in enumerate(case_names):
        values = [visual_data[cat][i] for cat in visual_categories]
        offset = (i - len(case_names)/2 + 0.5) * bar_width
        ax1.bar(x_visual + offset, values, bar_width, label=case_name, 
                color=colors[i], alpha=0.8)
    
    ax1.set_title('Visual Content Categories - Case Study Comparison', fontsize=32)
    ax1.set_xlabel('Categories', fontsize=18)
    ax1.set_ylabel('Count', fontsize=18)
    ax1.set_xticks(x_visual)
    ax1.set_xticklabels(visual_categories, rotation=45, ha='right', fontsize=14)
    ax1.tick_params(axis='y', labelsize=14)
    ax1.legend(fontsize=14)
    ax1.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('visual_category_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: visual_category_comparison.png")
    plt.show()
    
    # =========================================================================
    # AUDIO CATEGORIES PLOT
    # =========================================================================
    fig2 = plt.figure(figsize=(20, 10))
    ax2 = fig2.add_subplot(111)
    
    x_audio = np.arange(len(audio_categories))
    
    # Plot Audio categories
    for i, case_name in enumerate(case_names):
        values = [audio_data[cat][i] for cat in audio_categories]
        offset = (i - len(case_names)/2 + 0.5) * bar_width
        ax2.bar(x_audio + offset, values, bar_width, label=case_name,
                color=colors[i], alpha=0.8)
    
    ax2.set_title('Audio Content Categories - Case Study Comparison', fontsize=32)
    ax2.set_xlabel('Categories', fontsize=18)
    ax2.set_ylabel('Count', fontsize=18)
    ax2.set_xticks(x_audio)
    ax2.set_xticklabels(audio_categories, rotation=45, ha='right', fontsize=14)
    ax2.tick_params(axis='y', labelsize=14)
    ax2.legend(fontsize=14)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('audio_category_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: audio_category_comparison.png")
    plt.show()

# =============================================================================
# CONFIGURATION: Add your case studies here
# =============================================================================

# Define file paths and corresponding case study names
file_paths = [
    # 'memory_analysis.json',  # Example: current directory
    # Add more paths as needed, e.g.:
    '/Users/wen-chungcheng/remembr/results_20251029_042858_all_sounds_enabled_memories_PANN_audio_Phi3_vision_Command_r_RAG_full_test_standardized_queries/memory_analysis.json',
    '/Users/wen-chungcheng/remembr/results_20251029_044610_all_sounds_enabled_memories_ACT_audio_Gemma_3n_vision_Command_r_RAG_full_test_standardized_queries/memory_analysis.json',
    '/Users/wen-chungcheng/remembr/results_20251029_045912_all_sounds_enabled_memories_ACT_audio_Phi_3_vision_Command_r_RAG_full_test_standardized_queries/memory_analysis.json',
]

case_names = [
    'VLM: Phi3, ALM: PANN-CNN14, RAG LLM: Command-R',
    'VLM: Gemma 3n, ALM: ACT, RAG LLM: Command-R',
    'VLM: Phi3, ALM: ACT, RAG LLM: Command-R',
]

# =============================================================================
# RUN VISUALIZATION
# =============================================================================

# Load all case studies
case_studies = load_case_studies(file_paths, case_names)

# Generate comparison visualization
visualize_content_categories_comparison(case_studies)