
---

## 1. Position Accuracy Calculation

**Location:** `evaluate_navigation_performance()` method (lines ~760-830)

### Block 1: Distance Calculation

````python
                    distance = math.sqrt(
                        (expected_pos[0] - actual_pos[0])**2 + 
                        (expected_pos[1] - actual_pos[1])**2
                    )
````

**Explanation:**
- **`expected_pos`**: The ground truth coordinate (x, y) where a sound/object should be
- **`actual_pos`**: The coordinate extracted by the navigation service
- **Formula**: Standard Euclidean distance formula: $\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$
- **Purpose**: Measures how far off the navigation system is from the true location

### Block 2: Linear Decay Scoring

````python
                    # **FIXED: More realistic position accuracy calculation**
                    # Position accuracy: 1.0 at 0m distance, 0.0 at 100m+ distance (was 50m)
                    position_accuracy = max(0, 1 - (distance / 100.0))
````

**Line-by-line:**

1. **`distance / 100.0`**: 
   - Normalizes distance against a 100-meter threshold
   - Example: 25m distance → 0.25, 100m → 1.0, 150m → 1.5

2. **`1 - (...)`**: 
   - Inverts the normalized value
   - Example: 0.25 → 0.75 (75% accuracy), 1.0 → 0.0 (0% accuracy)

3. **`max(0, ...)`**: 
   - Prevents negative scores
   - If distance > 100m, score bottoms out at 0

**Scoring Scale:**
- **0 meters away** = 1.0 (100% accurate)
- **50 meters away** = 0.5 (50% accurate)
- **100 meters away** = 0.0 (0% accurate)
- **200 meters away** = still 0.0 (clamped)

### Block 3: Proximity Bonus

````python
                    # Give some credit for being in the right general area (within 200m)
                    if distance <= 200.0:
                        position_accuracy = max(position_accuracy, 0.2)  # Minimum 20% for being close
````

**Logic:**
- **Purpose**: Prevents harsh penalization for "close but not exact" predictions
- **Threshold**: If within 200 meters of target
- **Award**: Guarantees minimum score of 0.2 (20%)

**Example Scenarios:**
```
Distance = 50m  → Linear score = 0.5 → Final = 0.5 (no bonus needed)
Distance = 120m → Linear score = 0.0 → Final = 0.2 (bonus applied!)
Distance = 250m → Linear score = 0.0 → Final = 0.0 (too far, no bonus)
```

---

## 2. Relevance Score Calculation

**Location:** `_calculate_scenario_aware_query_relevance()` method (lines ~1060-1130)

This is a **two-component weighted score**: Content Matching + Position Matching

### Component A: Content-Based Relevance

#### Step 1: Audio Content Matching

````python
            if hasattr(result, 'audio_caption') and result.audio_caption:
                audio_text = result.audio_caption.lower()
                
                # Direct keyword matching
                query_words = set(query_text.split())
                audio_words = set(audio_text.split())
                overlap = len(query_words.intersection(audio_words))
                
                if overlap > 0:
                    content_score = max(content_score, overlap / len(query_words))
````

**Line-by-line breakdown:**

1. **`query_words = set(query_text.split())`**:
   - Splits query into individual words
   - Converts to **set** (removes duplicates, enables set operations)
   - Example: `"car horn sound"` → `{'car', 'horn', 'sound'}`

2. **`audio_words = set(audio_text.split())`**:
   - Same for memory's audio caption
   - Example: `"loud car horn honking"` → `{'loud', 'car', 'horn', 'honking'}`

3. **`overlap = len(query_words.intersection(audio_words))`**:
   - Counts words appearing in **both** sets
   - Example: `{'car', 'horn', 'sound'} ∩ {'loud', 'car', 'horn', 'honking'}` = `{'car', 'horn'}` → overlap = 2

4. **`content_score = max(..., overlap / len(query_words))`**:
   - Calculates **recall-based score**: what % of query words were found?
   - Example: 2 matches / 3 query words = 0.667 (66.7% score)
   - `max()` ensures we keep the **best** score across audio/visual

#### Step 2: Visual Content Matching

````python
            if result.caption:
                caption_text = result.caption
                if isinstance(caption_text, list):
                    caption_text = ' '.join(caption_text)
                
                caption_text = caption_text.lower()
                
                query_words = set(query_text.split())
                caption_words = set(caption_text.split())
                overlap = len(query_words.intersection(caption_words))
                
                if overlap > 0:
                    content_score = max(content_score, overlap / len(query_words))
````

**Same logic as audio matching, but for visual captions:**
- Handles both string and list caption formats
- Uses same word overlap calculation
- Updates `content_score` if visual match is better than audio match

---

### Component B: Position-Based Relevance

````python
            position_score = 0.0
            expected_position = query.get('expected_position')
            if expected_position and hasattr(result, 'position') and result.position:
                distance = math.sqrt(
                    (expected_position[0] - result.position[0])**2 + 
                    (expected_position[1] - result.position[1])**2
                )
                # More generous position scoring
                position_score = max(0, 1 - (distance / 100.0))
````

**Line-by-line:**

1. **`expected_position = query.get('expected_position')`**:
   - Retrieves the ground truth location (if query specifies one)
   - Returns `None` if query doesn't have a position component

2. **Distance calculation**: (same as navigation accuracy above)
   - Euclidean distance between expected and actual memory position

3. **`position_score = max(0, 1 - (distance / 100.0))`**:
   - Identical linear decay as navigation accuracy
   - 100m threshold: 1.0 at 0m, 0.0 at 100m+

---

### Component C: Weighted Combination

````python
            # Weighted combination based on query category
            if category == 'direct_audio_match':
                score = content_score * 0.9 + position_score * 0.1
            elif category == 'direct_visual_match':
                score = content_score * 0.9 + position_score * 0.1
            elif category == 'multimodal_combo':
                score = content_score * 0.8 + position_score * 0.2
            elif category == 'position_based':
                score = content_score * 0.5 + position_score * 0.5
            else:
                score = content_score * 0.7 + position_score * 0.3
````

**Category-Specific Weighting:**

| Query Category | Content Weight | Position Weight | Use Case |
|----------------|----------------|-----------------|----------|
| **direct_audio_match** | 90% | 10% | "Find car horn" - content is king |
| **direct_visual_match** | 90% | 10% | "Find building" - content is king |
| **multimodal_combo** | 80% | 20% | "Car horn near fence" - balanced |
| **position_based** | 50% | 50% | "Sounds at (10, 20)" - location matters |
| **default** | 70% | 30% | Generic queries |

**Example Calculation:**

```python
# Scenario: Query = "car horn near fence" (multimodal_combo)
content_score = 0.75  # 75% word overlap
position_score = 0.4  # 60m away

final_score = 0.75 * 0.8 + 0.4 * 0.2
            = 0.6 + 0.08
            = 0.68 (68% relevance)
```

---

### Final Aggregation

````python
            relevance_scores.append(score)
        
        # Return best relevance score
        return max(relevance_scores) if relevance_scores else 0.0
````

**Logic:**
- Calculates scores for **all** retrieved memories
- Returns the **maximum** score (best matching memory)
- Rationale: If even one memory is highly relevant, the retrieval succeeds

---

## Key Design Decisions

### Position Accuracy
1. **100m threshold**: Realistic for urban robot navigation
2. **20% proximity bonus**: Rewards "general area" understanding
3. **No negative scores**: Failures capped at 0

### Relevance Scores
1. **Recall-based matching**: Favors finding all query words
2. **Category-aware weighting**: Different tasks prioritize content vs. position
3. **Best-match selection**: One good result = successful retrieval

This dual-metric system evaluates both **coordinate precision** (position accuracy) and **semantic understanding** (relevance), providing comprehensive assessment of your multimodal memory system!