#!/bin/bash

# Complete Multimodal Memory Evaluation Pipeline with Isolated Sound Benchmarking
echo "🎯 Multimodal Memory Building Evaluation Pipeline with Isolated Sound Tests"
echo "========================================================================="

# Configuration
WORLD_FILE="/Users/wen-chungcheng/Documents/Webots Sims/vehicles/worlds/village_center_pioneer3at.wbt"
SOUND_CONTROLLER="/Users/wen-chungcheng/Documents/Webots Sims/vehicles/controllers/master_sound_controller/master_sound_controller.py"
COLLECTION_NAME="webots_sounds_multimodal"
DB_IP="127.0.0.1"
EVAL_DIR="/Users/wen-chungcheng/remembr"
OUTPUT_DIR="$EVAL_DIR/results_$(date +%Y%m%d_%H%M%S)"

# Model Configuration
MODEL_BACKEND="COMMAND_R"  # Options: COMMAND_R, GEMMA

# Parse command line arguments for model backend
while [[ $# -gt 0 ]]; do
    case $1 in
        --model-backend)
            MODEL_BACKEND="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--model-backend COMMAND_R|GEMMA]"
            echo "  --model-backend: Choose model backend (COMMAND_R or GEMMA)"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

echo "🤖 Using model backend: $MODEL_BACKEND"

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "📁 Output directory: $OUTPUT_DIR"

# Set environment
export PYTHONPATH="/Users/wen-chungcheng/remembr:/Users/wen-chungcheng/ACT:$PYTHONPATH"
cd "$EVAL_DIR"

# Step 1: Generate Ground Truth Labels
echo ""
echo "🏷️ Step 1: Generating ground truth labels..."
python ground_truth_labeler.py \
    --world-file "$WORLD_FILE" \
    --sound-controller "$SOUND_CONTROLLER" \
    --output "$OUTPUT_DIR/ground_truth.json"

if [ $? -ne 0 ]; then
    echo "❌ Ground truth generation failed"
    exit 1
fi

# Step 2: Analyze Memory Content
echo ""
echo "🔍 Step 2: Analyzing memory content..."
python memory_content_analyzer.py \
    --collection "$COLLECTION_NAME" \
    --db-ip "$DB_IP" \
    --output "$OUTPUT_DIR/memory_analysis.json"

if [ $? -ne 0 ]; then
    echo "❌ Memory content analysis failed"
    exit 1
fi

# Step 3: Run Comprehensive Evaluation
echo ""
echo "🚀 Step 3: Running comprehensive evaluation with $MODEL_BACKEND..."
python multimodal_evaluation_framework.py \
    --ground-truth "$OUTPUT_DIR/ground_truth.json" \
    --collection "$COLLECTION_NAME" \
    --db-ip "$DB_IP" \
    --model-backend "$MODEL_BACKEND" \
    --output "$OUTPUT_DIR/evaluation_report.json"

if [ $? -ne 0 ]; then
    echo "❌ Comprehensive evaluation failed"
    exit 1
fi

# Step 4: Run Isolated Sound Evaluation (NEW)
echo ""
echo "🎯 Step 4: Running isolated sound evaluation with $MODEL_BACKEND..."
python isolated_sound_evaluator.py \
    --ground-truth "$OUTPUT_DIR/ground_truth.json" \
    --collection "$COLLECTION_NAME" \
    --db-ip "$DB_IP" \
    --model-backend "$MODEL_BACKEND" \
    --output "$OUTPUT_DIR/isolated_sound_evaluation.json"

if [ $? -ne 0 ]; then
    echo "❌ Isolated sound evaluation failed"
    exit 1
fi

# Step 5: Generate Comprehensive Report
echo ""
echo "📊 Step 5: Generating comprehensive evaluation report..."

# Create isolated sound benchmark configuration
cat > "$OUTPUT_DIR/isolated_sound_config.json" << EOF
{
    "auto_start": false,
    "test_duration": 30.0,
    "sequential_tests": true,
    "enabled_sources": "all",
    "test_scenarios": [
        {"name": "baseline_no_sounds", "enabled_sources": []},
        {"name": "church_bell_only", "enabled_sources": ["church_bell_speaker"]},
        {"name": "ambient_only", "enabled_sources": ["city_amb_speaker_1", "city_amb_speaker_2"]},
        {"name": "car_sounds_only", "enabled_sources": ["car_honk_speaker_1", "car_honk_speaker_2"]},
        {"name": "help_sounds_only", "enabled_sources": ["help_sound_speaker_1", "help_sound_speaker_2"]},
        {"name": "ambulance_sirens_only", "enabled_sources": ["ambulance_speaker_1", "ambulance_speaker_2"]},
        {"name": "all_enabled", "enabled_sources": "all"}
    ]
}
EOF

# Create comprehensive HTML report
cat > "$OUTPUT_DIR/comprehensive_evaluation_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Comprehensive Multimodal Memory Evaluation Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background-color: #f8f9fa;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px; 
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric { 
            background: #f8f9fa;
            padding: 20px; 
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .score { 
            font-size: 32px; 
            font-weight: bold; 
            color: #2e8b57;
            margin: 10px 0;
        }
        .label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .file-list {
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .file-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 5px;
        }
        .emoji { font-size: 20px; margin-right: 10px; }
        h2 { color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
        h3 { color: #495057; }
        .highlight { background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Comprehensive Multimodal Memory Evaluation</h1>
        <h2>Including Isolated Sound Benchmark Analysis</h2>
        <p>Generated on $(date)</p>
        <p>Collection: $COLLECTION_NAME</p>
        <p>Model Backend: $MODEL_BACKEND</p>
    </div>
    
    <div class="section">
        <h2>📊 Evaluation Overview</h2>
        <p>This comprehensive evaluation includes both standard multimodal memory analysis and specialized isolated sound benchmarking to understand the contribution of individual sound sources to memory building performance.</p>
        
        <div class="highlight">
            <strong>🆕 New in this evaluation:</strong> Isolated sound benchmarking allows you to understand which individual sound sources contribute most effectively to memory building and retrieval performance.
        </div>
    </div>
    
    <div class="section">
        <h2>📁 Generated Files</h2>
        <div class="file-list">
            <div class="file-item">
                <span class="emoji">🏷️</span>
                <div>
                    <strong>ground_truth.json</strong><br>
                    <small>Automatically extracted ground truth labels from world file and sound controller</small>
                </div>
            </div>
            <div class="file-item">
                <span class="emoji">🔍</span>
                <div>
                    <strong>memory_analysis.json</strong><br>
                    <small>Detailed analysis of stored multimodal memories</small>
                </div>
            </div>
            <div class="file-item">
                <span class="emoji">🚀</span>
                <div>
                    <strong>evaluation_report.json</strong><br>
                    <small>Comprehensive evaluation including navigation performance</small>
                </div>
            </div>
            <div class="file-item">
                <span class="emoji">🎯</span>
                <div>
                    <strong>isolated_sound_evaluation.json</strong><br>
                    <small>Isolated sound source performance analysis</small>
                </div>
            </div>
            <div class="file-item">
                <span class="emoji">⚙️</span>
                <div>
                    <strong>isolated_sound_config.json</strong><br>
                    <small>Configuration for isolated sound benchmark testing</small>
                </div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🎮 Using the Isolated Sound Benchmark Controller</h2>
        <h3>Manual Testing</h3>
        <p>Use the isolated sound benchmark controller for interactive testing:</p>
        <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
cd /Users/wen-chungcheng/Documents/Webots\ Sims/vehicles/controllers/isolated_sound_benchmark_controller/
python isolated_sound_benchmark_controller.py --config "$OUTPUT_DIR/isolated_sound_config.json"
        </pre>
        
        <h3>Keyboard Controls</h3>
        <div class="metric-grid">
            <div class="metric">
                <div class="label">Toggle Sounds</div>
                <div style="font-size: 20px; color: #007bff;">1-9</div>
            </div>
            <div class="metric">
                <div class="label">Enable All</div>
                <div style="font-size: 20px; color: #28a745;">A</div>
            </div>
            <div class="metric">
                <div class="label">Disable All</div>
                <div style="font-size: 20px; color: #dc3545;">D</div>
            </div>
            <div class="metric">
                <div class="label">Benchmark Mode</div>
                <div style="font-size: 20px; color: #ffc107;">B</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Next Steps</h2>
        <ol>
            <li><strong>Review the evaluation results</strong> in the JSON files</li>
            <li><strong>Run isolated sound tests</strong> using the benchmark controller</li>
            <li><strong>Analyze which sound types</strong> contribute most to memory building</li>
            <li><strong>Optimize sound placement</strong> based on effectiveness rankings</li>
            <li><strong>Iterate and improve</strong> your multimodal memory system</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>🔗 Related Tools</h2>
        <ul>
            <li><strong>Memory Inspector:</strong> milvus_memory_inspector_multimodal.py</li>
            <li><strong>Content Analyzer:</strong> memory_content_analyzer.py</li>
            <li><strong>Evaluation Framework:</strong> multimodal_evaluation_framework.py</li>
            <li><strong>Sound Benchmark:</strong> isolated_sound_evaluator.py</li>
        </ul>
    </div>
</body>
</html>
EOF

# Add this section after Step 5 in the existing script

# Step 5.5: Generate Enhanced HTML Report with Scenario Breakdown
echo ""
echo "📊 Step 5.5: Generating enhanced scenario-aware report..."

# Create enhanced HTML report with scenario breakdown
cat > "$OUTPUT_DIR/scenario_aware_evaluation_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Scenario-Aware Multimodal Memory Evaluation Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background-color: #f8f9fa;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px; 
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric { 
            background: #f8f9fa;
            padding: 20px; 
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .score { 
            font-size: 32px; 
            font-weight: bold; 
            color: #2e8b57;
            margin: 10px 0;
        }
        .score.low { color: #dc3545; }
        .score.medium { color: #ffc107; }
        .score.high { color: #28a745; }
        .label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .scenario-breakdown {
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .scenario-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 8px 0;
            padding: 12px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .scenario-item.car-sound { border-left-color: #28a745; }
        .scenario-item.baseline { border-left-color: #17a2b8; }
        .scenario-item.non-existent { border-left-color: #dc3545; }
        h2 { color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
        h3 { color: #495057; }
        .highlight { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .success { background: #d4edda; border-left: 4px solid #28a745; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; }
        .danger { background: #f8d7da; border-left: 4px solid #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Scenario-Aware Multimodal Memory Evaluation</h1>
        <h2>Enhanced with Realistic Query Testing</h2>
        <p>Generated on $(date)</p>
        <p>Collection: $COLLECTION_NAME</p>
    </div>
    
    <div class="section">
        <h2>🆕 What's New in This Evaluation</h2>
        <div class="highlight success">
            <h3>✅ Scenario-Aware Retrieval Testing</h3>
            <p>This evaluation now tests retrieval performance with queries that match your actual memory content:</p>
            <ul>
                <li><strong>Car Sound Queries:</strong> Tests for car horn/honking sounds (should have high success rates)</li>
                <li><strong>Visual Content Queries:</strong> Tests for buildings, fences, trash bins (moderate success expected)</li>
                <li><strong>Non-existent Sound Queries:</strong> Tests for church bells, screaming (should appropriately fail)</li>
                <li><strong>Multimodal Queries:</strong> Combines audio and visual elements</li>
            </ul>
        </div>
        
        <div class="highlight warning">
            <h3>📊 More Realistic Success Thresholds</h3>
            <p>Different query types now use appropriate success thresholds:</p>
            <ul>
                <li>Car sound queries: 30% relevance threshold</li>
                <li>Visual queries: 20% relevance threshold</li>
                <li>Non-existent sounds: 10% relevance threshold</li>
            </ul>
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Expected Results</h2>
        <div class="scenario-breakdown">
            <h3>Scenario Performance Expectations:</h3>
            
            <div class="scenario-item car-sound">
                <div>
                    <strong>🚗 Car Sound Queries</strong><br>
                    <small>Should achieve 60-80% success rate since your memories contain car horn sounds</small>
                </div>
                <div class="score high">HIGH</div>
            </div>
            
            <div class="scenario-item baseline">
                <div>
                    <strong>👁️ Visual Content Queries</strong><br>
                    <small>Should achieve 30-50% success rate for buildings, fences, trash bins</small>
                </div>
                <div class="score medium">MED</div>
            </div>
            
            <div class="scenario-item non-existent">
                <div>
                    <strong>🔕 Non-existent Sound Queries</strong><br>
                    <small>Should achieve 0-20% success rate (appropriately low for absent sounds)</small>
                </div>
                <div class="score low">LOW</div>
            </div>

            <div class="scenario-item non-existent">
                <div>
                    <strong>🚑 Ambulance Siren Queries</strong><br>
                    <small>Should achieve 0-20% success rate if no ambulance sounds are present</small>
                </div>
                <div class="score low">LOW</div>
            </div>

        </div>
    </div>
    
    <div class="section">
        <h2>🔍 Key Improvements</h2>
        <ul>
            <li><strong>Content Analysis:</strong> Queries generated based on actual memory content</li>
            <li><strong>Scenario Alignment:</strong> Retrieval tests match isolated sound evaluation scenarios</li>
            <li><strong>Realistic Thresholds:</strong> Success criteria adjusted for different content types</li>
            <li><strong>Detailed Breakdown:</strong> Performance reported by scenario and query type</li>
            <li><strong>Navigation Alignment:</strong> Navigation queries also scenario-aware</li>
        </ul>
    </div>
</body>
</html>
EOF

echo "   📊 Enhanced scenario-aware report generated"

# Step 6: Display Results
echo ""
echo "✅ Comprehensive evaluation pipeline completed successfully!"
echo ""
echo "📁 Results saved to: $OUTPUT_DIR"
echo "📋 Files generated:"
echo "   🏷️ ground_truth.json - Ground truth labels"
echo "   🔍 memory_analysis.json - Memory content analysis" 
echo "   🚀 evaluation_report.json - Comprehensive evaluation"
echo "   🎯 isolated_sound_evaluation.json - Isolated sound analysis"
echo "   ⚙️ isolated_sound_config.json - Benchmark configuration"
echo "   📊 comprehensive_evaluation_report.html - Visual summary"
echo ""

# Quick preview of results
if command -v jq >/dev/null 2>&1; then
    echo "🏆 Quick Results Preview:"
    echo "------------------------"
    
    if [ -f "$OUTPUT_DIR/evaluation_report.json" ]; then
        echo "📊 Standard Evaluation:"
        echo "  Overall System Score: $(jq -r '.overall_scores.overall_system_score // "N/A"' "$OUTPUT_DIR/evaluation_report.json")"
        echo "  Spatial Coverage: $(jq -r '.overall_scores.spatial_coverage // "N/A"' "$OUTPUT_DIR/evaluation_report.json")"
        echo "  Content Accuracy: $(jq -r '.overall_scores.content_accuracy // "N/A"' "$OUTPUT_DIR/evaluation_report.json")"
    fi
    
    if [ -f "$OUTPUT_DIR/isolated_sound_evaluation.json" ]; then
        echo ""
        echo "🎯 Isolated Sound Analysis:"
        echo "  Best Sound Type: $(jq -r '.comparative_analysis.best_performing_sound_type.type // "N/A"' "$OUTPUT_DIR/isolated_sound_evaluation.json")"
        echo "  Best Score: $(jq -r '.comparative_analysis.best_performing_sound_type.score // "N/A"' "$OUTPUT_DIR/isolated_sound_evaluation.json")"
    fi
else
    echo "💡 Install 'jq' for JSON result preview: brew install jq"
fi

echo ""
echo "🎮 To run isolated sound benchmarks manually:"
echo "   cd /Users/wen-chungcheng/Documents/Webots\ Sims/vehicles/controllers/isolated_sound_benchmark_controller/"
echo "   python isolated_sound_benchmark_controller.py --config \"$OUTPUT_DIR/isolated_sound_config.json\""
echo ""
echo "🎉 Comprehensive evaluation with isolated sound benchmarking complete!"