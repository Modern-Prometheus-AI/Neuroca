#!/usr/bin/env python3
"""
Script to generate architectural diagram documentation for the NeuroCognitive Architecture.
This script creates Markdown files with Mermaid diagrams for various components of the system.
"""

import os
import sys
from pathlib import Path

# Base directory for diagrams
DOCS_DIR = Path("docs/architecture/diagrams")

# Template for Mermaid diagrams (dark theme)
MERMAID_TEMPLATE = '''```mermaid
%%{{init: {{'theme': 'dark', 'themeVariables': {{ 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}}}}%%
{diagram_type}
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    {class_defs}

    {diagram_content}
```'''

# Template for Markdown files
MARKDOWN_TEMPLATE = '''# {title}

{description}

{diagram}

## {section_title}

{section_content}
'''

# Ensure directory exists
def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)

# Components Dictionary - Maps file paths to content
COMPONENTS = {
    # Cognitive Control Components
    "cognitive-control/components/goals.md": {
        "title": "Goal Management System",
        "description": "This diagram details the goal management component of the NeuroCognitive Architecture (NCA) cognitive control system.",
        "diagram_type": "graph TB",
        "class_defs": "classDef goal fill:#203020,stroke:#555,color:#fff\nclassDef process fill:#252525,stroke:#555,color:#fff",
        "diagram_content": '''subgraph GoalSystem["Goal Management System"]
        direction TB
        class GoalSystem main
        
        subgraph GoalRepresentation["Goal Representation"]
            direction TB
            class GoalRepresentation goal
            GoalStructure[Goal<br>Structure] --- GoalMetadata[Goal<br>Metadata]
            GoalState[Goal<br>State] --- GoalContext[Goal<br>Context]
            class GoalStructure,GoalMetadata,GoalState,GoalContext subcomponent
        end
        
        subgraph GoalPrioritization["Goal Prioritization"]
            direction TB
            class GoalPrioritization goal
            PriorityCalculation[Priority<br>Calculation] --- Urgency[Urgency<br>Assessment]
            Importance[Importance<br>Assessment] --- Feasibility[Feasibility<br>Analysis]
            class PriorityCalculation,Urgency,Importance,Feasibility subcomponent
        end
        
        subgraph GoalMaintenance["Goal Maintenance"]
            direction TB
            class GoalMaintenance goal
            ActiveGoals[Active<br>Goals] --- GoalPersistence[Goal<br>Persistence]
            GoalRefresh[Goal<br>Refresh] --- GoalActivation[Goal<br>Activation]
            class ActiveGoals,GoalPersistence,GoalRefresh,GoalActivation subcomponent
        end
        
        subgraph GoalResolution["Goal Resolution"]
            direction TB
            class GoalResolution goal
            ConflictDetection[Conflict<br>Detection] --- ConflictResolution[Conflict<br>Resolution]
            GoalSelection[Goal<br>Selection] --- GoalAdjustment[Goal<br>Adjustment]
            class ConflictDetection,ConflictResolution,GoalSelection,GoalAdjustment subcomponent
        end
        
        subgraph GoalDecomposition["Goal Decomposition"]
            direction TB
            class GoalDecomposition goal
            TaskAnalysis[Task<br>Analysis] --- SubgoalCreation[Subgoal<br>Creation]
            DependencyAnalysis[Dependency<br>Analysis] --- PlanAlignment[Plan<br>Alignment]
            class TaskAnalysis,SubgoalCreation,DependencyAnalysis,PlanAlignment subcomponent
        end
        
        subgraph GoalTracking["Goal Tracking"]
            direction TB
            class GoalTracking goal
            ProgressMonitoring[Progress<br>Monitoring] --- Completion[Completion<br>Detection]
            Success[Success<br>Evaluation] --- Failure[Failure<br>Analysis]
            class ProgressMonitoring,Completion,Success,Failure subcomponent
        end
    end
    
    %% External connections
    WorkingMemory[Working<br>Memory] --> GoalRepresentation
    AttentionSystem[Attention<br>System] --> GoalPrioritization
    
    %% Internal connections
    GoalRepresentation --> GoalPrioritization
    GoalPrioritization --> GoalMaintenance
    GoalMaintenance --> GoalResolution
    GoalResolution --> GoalDecomposition
    GoalDecomposition --> GoalTracking
    
    %% Feedback loops
    GoalTracking --> GoalRepresentation
    
    class WorkingMemory,AttentionSystem subcomponent''',
        "section_title": "Goal Management System Components",
        "section_content": '''The Goal Management System is responsible for representing, prioritizing, maintaining, and tracking goals within the cognitive architecture. It includes the following key components:

### Goal Representation
- **Goal Structure**: Defines the format and components of a goal
- **Goal Metadata**: Additional information about the goal (creation time, source, etc.)
- **Goal State**: Current status of the goal (active, completed, failed, etc.)
- **Goal Context**: The context in which the goal is relevant

### Goal Prioritization
- **Priority Calculation**: Determines the relative importance of goals
- **Urgency Assessment**: Evaluates time sensitivity of goals
- **Importance Assessment**: Evaluates value or significance of goals
- **Feasibility Analysis**: Assesses the likelihood of successful goal completion

### Goal Maintenance
- **Active Goals**: Manages the set of currently active goals
- **Goal Persistence**: Maintains goals over time
- **Goal Refresh**: Updates goal information as context changes
- **Goal Activation**: Activates relevant goals based on context

### Goal Resolution
- **Conflict Detection**: Identifies conflicts between competing goals
- **Conflict Resolution**: Resolves conflicts through prioritization or compromise
- **Goal Selection**: Chooses which goals to pursue when resources are limited
- **Goal Adjustment**: Modifies goals based on changing conditions

### Goal Decomposition
- **Task Analysis**: Breaks down goals into manageable components
- **Subgoal Creation**: Creates subordinate goals that support the main goal
- **Dependency Analysis**: Identifies dependencies between goals and subgoals
- **Plan Alignment**: Ensures subgoals align with the overall plan

### Goal Tracking
- **Progress Monitoring**: Tracks progress toward goal completion
- **Completion Detection**: Identifies when goals have been achieved
- **Success Evaluation**: Assesses the degree of success in goal achievement
- **Failure Analysis**: Analyzes reasons for goal failure

The Goal Management System interacts with the Working Memory to store active goals and with the Attention System to direct focus toward high-priority goals. It maintains a continuous feedback loop between goal tracking and representation to adapt goals based on progress and changing conditions.'''
    },
    
    "cognitive-control/components/inhibition.md": {
        "title": "Inhibition System",
        "description": "This diagram details the inhibition component of the NeuroCognitive Architecture (NCA) cognitive control system.",
        "diagram_type": "graph TB",
        "class_defs": "classDef inhibition fill:#302020,stroke:#555,color:#fff\nclassDef process fill:#252525,stroke:#555,color:#fff",
        "diagram_content": '''subgraph InhibitionSystem["Inhibition System"]
        direction TB
        class InhibitionSystem main
        
        subgraph ResponseInhibition["Response Inhibition"]
            direction TB
            class ResponseInhibition inhibition
            PrepotentSuppression[Prepotent<br>Suppression] --- ActionCancel[Action<br>Cancellation]
            ResponseDelay[Response<br>Delay] --- ActionSelection[Action<br>Selection<br>Filter]
            class PrepotentSuppression,ActionCancel,ResponseDelay,ActionSelection subcomponent
        end
        
        subgraph DistractorSuppression["Distractor Suppression"]
            direction TB
            class DistractorSuppression inhibition
            SalienceFiltering[Salience<br>Filtering] --- NoiseReduction[Noise<br>Reduction]
            RelevanceFilter[Relevance<br>Filter] --- FocusProtection[Focus<br>Protection]
            class SalienceFiltering,NoiseReduction,RelevanceFilter,FocusProtection subcomponent
        end
        
        subgraph InterferenceControl["Interference Control"]
            direction TB
            class InterferenceControl inhibition
            CrossTalkPrevention[Cross-Talk<br>Prevention] --- ContextProtection[Context<br>Protection]
            MemoryInterference[Memory<br>Interference<br>Control] --- ProcessIsolation[Process<br>Isolation]
            class CrossTalkPrevention,ContextProtection,MemoryInterference,ProcessIsolation subcomponent
        end
        
        subgraph PrepotentInhibition["Prepotent Inhibition"]
            direction TB
            class PrepotentInhibition inhibition
            HabitOverride[Habit<br>Override] --- AutomaticControl[Automatic<br>Response<br>Control]
            DefaultOverride[Default<br>Override] --- PatternInterrupt[Pattern<br>Interrupt]
            class HabitOverride,AutomaticControl,DefaultOverride,PatternInterrupt subcomponent
        end
        
        subgraph CognitiveSuppression["Cognitive Suppression"]
            direction TB
            class CognitiveSuppression inhibition
            ThoughtSuppression[Thought<br>Suppression] --- MemorySuppression[Memory<br>Suppression]
            ConceptInhibition[Concept<br>Inhibition] --- AssociationBlocking[Association<br>Blocking]
            class ThoughtSuppression,MemorySuppression,ConceptInhibition,AssociationBlocking subcomponent
        end
        
        subgraph EmotionalRegulation["Emotional Regulation"]
            direction TB
            class EmotionalRegulation inhibition
            EmotionSuppression[Emotion<br>Suppression] --- AffectiveControl[Affective<br>Control]
            EmotionalBias[Emotional<br>Bias<br>Reduction] --- EmotionReappraisal[Emotion<br>Reappraisal]
            class EmotionSuppression,AffectiveControl,EmotionalBias,EmotionReappraisal subcomponent
        end
    end
    
    %% External connections
    ExecutiveFunction[Executive<br>Function] --> ResponseInhibition
    AttentionSystem[Attention<br>System] --> DistractorSuppression
    
    %% Internal connections
    ResponseInhibition --> InterferenceControl
    DistractorSuppression --> InterferenceControl
    InterferenceControl --> PrepotentInhibition
    PrepotentInhibition --> CognitiveSuppression
    CognitiveSuppression --> EmotionalRegulation
    
    %% Cross-connections
    DistractorSuppression --> ResponseInhibition
    EmotionalRegulation --> ResponseInhibition
    
    class ExecutiveFunction,AttentionSystem subcomponent''',
        "section_title": "Inhibition System Components",
        "section_content": '''The Inhibition System is responsible for suppressing inappropriate responses, filtering distractions, and managing interference in cognitive processes. It includes the following key components:

### Response Inhibition
- **Prepotent Suppression**: Suppresses dominant or automatic responses
- **Action Cancellation**: Stops actions that have been initiated
- **Response Delay**: Introduces a delay before responding to allow for evaluation
- **Action Selection Filter**: Filters out inappropriate actions from the selection process

### Distractor Suppression
- **Salience Filtering**: Reduces the impact of salient but irrelevant stimuli
- **Noise Reduction**: Filters out background noise in sensory and cognitive processing
- **Relevance Filter**: Allows only contextually relevant information to pass through
- **Focus Protection**: Maintains attention on the current task by suppressing distractions

### Interference Control
- **Cross-Talk Prevention**: Prevents interference between concurrent processes
- **Context Protection**: Maintains the integrity of contextual information
- **Memory Interference Control**: Manages interference between memory items
- **Process Isolation**: Ensures isolation between cognitive processes that might interfere

### Prepotent Inhibition
- **Habit Override**: Overrides habitual responses in favor of goal-directed behavior
- **Automatic Response Control**: Regulates automatic responses based on context
- **Default Override**: Suppresses default behaviors when they are inappropriate
- **Pattern Interrupt**: Breaks established patterns of thinking or behavior

### Cognitive Suppression
- **Thought Suppression**: Inhibits intrusive or irrelevant thoughts
- **Memory Suppression**: Temporarily inhibits memory retrieval when it would interfere
- **Concept Inhibition**: Suppresses activation of concepts that are not contextually relevant
- **Association Blocking**: Blocks inappropriate associations between concepts

### Emotional Regulation
- **Emotion Suppression**: Dampens emotional responses when they would interfere with cognition
- **Affective Control**: Regulates the influence of affect on cognitive processes
- **Emotional Bias Reduction**: Reduces biases introduced by emotional states
- **Emotion Reappraisal**: Reframes emotional reactions to change their impact

The Inhibition System is closely linked to the Executive Function system, which directs inhibitory control, and the Attention System, which works in tandem with Distractor Suppression to maintain focus. Inhibition is a critical function in cognitive control, allowing for flexible, goal-directed behavior by suppressing inappropriate responses and irrelevant information.'''
    },
    
    "cognitive-control/components/metacognition.md": {
        "title": "Metacognition System",
        "description": "This diagram details the metacognition component of the NeuroCognitive Architecture (NCA) cognitive control system.",
        "diagram_type": "graph TB",
        "class_defs": "classDef metacognition fill:#203030,stroke:#555,color:#fff\nclassDef process fill:#252525,stroke:#555,color:#fff",
        "diagram_content": '''subgraph MetacognitionSystem["Metacognition System"]
        direction TB
        class MetacognitionSystem main
        
        subgraph SelfMonitoring["Self-Monitoring"]
            direction TB
            class SelfMonitoring metacognition
            ProcessMonitoring[Process<br>Monitoring] --- StateAwareness[State<br>Awareness]
            PerformanceTracking[Performance<br>Tracking] --- ResourceMonitoring[Resource<br>Monitoring]
            class ProcessMonitoring,StateAwareness,PerformanceTracking,ResourceMonitoring subcomponent
        end
        
        subgraph ReflectionSystem["Reflection System"]
            direction TB
            class ReflectionSystem metacognition
            SelfEvaluation[Self<br>Evaluation] --- ProcessAnalysis[Process<br>Analysis]
            HistoricalReview[Historical<br>Review] --- OutcomeAnalysis[Outcome<br>Analysis]
            class SelfEvaluation,ProcessAnalysis,HistoricalReview,OutcomeAnalysis subcomponent
        end
        
        subgraph ErrorDetection["Error Detection"]
            direction TB
            class ErrorDetection metacognition
            ErrorRecognition[Error<br>Recognition] --- ConflictDetection[Conflict<br>Detection]
            ExpectationViolation[Expectation<br>Violation] --- AnomalyDetection[Anomaly<br>Detection]
            class ErrorRecognition,ConflictDetection,ExpectationViolation,AnomalyDetection subcomponent
        end
        
        subgraph StrategyAdaptation["Strategy Adaptation"]
            direction TB
            class StrategyAdaptation metacognition
            StrategySelection[Strategy<br>Selection] --- StrategyAdjustment[Strategy<br>Adjustment]
            ApproachRefinement[Approach<br>Refinement] --- MethodSwitching[Method<br>Switching]
            class StrategySelection,StrategyAdjustment,ApproachRefinement,MethodSwitching subcomponent
        end
        
        subgraph ConfidenceEstimation["Confidence Estimation"]
            direction TB
            class ConfidenceEstimation metacognition
            CertaintyAssessment[Certainty<br>Assessment] --- UncertaintyQuantification[Uncertainty<br>Quantification]
            ReliabilityRating[Reliability<br>Rating] --- PrecisionEstimation[Precision<br>Estimation]
            class CertaintyAssessment,UncertaintyQuantification,ReliabilityRating,PrecisionEstimation subcomponent
        end
        
        subgraph IntrospectionSystem["Introspection System"]
            direction TB
            class IntrospectionSystem metacognition
            SelfUnderstanding[Self<br>Understanding] --- KnowledgeAssessment[Knowledge<br>Assessment]
            AbilityEvaluation[Ability<br>Evaluation] --- LimitAwareness[Limit<br>Awareness]
            class SelfUnderstanding,KnowledgeAssessment,AbilityEvaluation,LimitAwareness subcomponent
        end
    end
    
    %% External connections
    ExecutiveFunction[Executive<br>Function] --> SelfMonitoring
    MemorySystem[Memory<br>System] --> ReflectionSystem
    
    %% Internal connections
    SelfMonitoring --> ReflectionSystem
    ReflectionSystem --> ErrorDetection
    ErrorDetection --> StrategyAdaptation
    StrategyAdaptation --> ConfidenceEstimation
    ConfidenceEstimation --> IntrospectionSystem
    
    %% Feedback loops
    IntrospectionSystem --> SelfMonitoring
    StrategyAdaptation --> SelfMonitoring
    
    %% System-wide metacognitive oversight
    SelfMonitoring --> CognitiveSystem[Cognitive<br>Control<br>System]
    ReflectionSystem --> LearningSystem[Learning<br>System]
    ConfidenceEstimation --> DecisionSystem[Decision<br>Making<br>System]
    
    class ExecutiveFunction,MemorySystem,CognitiveSystem,LearningSystem,DecisionSystem subcomponent''',
        "section_title": "Metacognition System Components",
        "section_content": '''The Metacognition System enables self-reflection, error detection, and strategy adaptation in the cognitive architecture. It includes the following key components:

### Self-Monitoring
- **Process Monitoring**: Tracks the execution of cognitive processes
- **State Awareness**: Maintains awareness of current cognitive and system states
- **Performance Tracking**: Monitors performance metrics and outcomes
- **Resource Monitoring**: Tracks utilization of computational and cognitive resources

### Reflection System
- **Self-Evaluation**: Evaluates the quality and effectiveness of cognitive processing
- **Process Analysis**: Analyzes the steps and methods used in cognitive operations
- **Historical Review**: Examines past performance and learning
- **Outcome Analysis**: Analyzes the results of cognitive operations against expectations

### Error Detection
- **Error Recognition**: Identifies mistakes in processing or outputs
- **Conflict Detection**: Detects contradictions or inconsistencies
- **Expectation Violation**: Recognizes when outcomes differ from expectations
- **Anomaly Detection**: Identifies unusual patterns or deviations from norms

### Strategy Adaptation
- **Strategy Selection**: Chooses appropriate cognitive strategies based on context
- **Strategy Adjustment**: Modifies strategies in response to performance feedback
- **Approach Refinement**: Fine-tunes approaches based on outcomes
- **Method Switching**: Changes methods when current approaches are ineffective

### Confidence Estimation
- **Certainty Assessment**: Evaluates confidence in knowledge or decisions
- **Uncertainty Quantification**: Measures degree of uncertainty
- **Reliability Rating**: Assesses the reliability of information or processes
- **Precision Estimation**: Estimates the precision of knowledge or predictions

### Introspection System
- **Self-Understanding**: Develops models of own cognitive processes
- **Knowledge Assessment**: Evaluates what is known and unknown
- **Ability Evaluation**: Assesses capabilities and limitations
- **Limit Awareness**: Recognizes boundaries of knowledge or abilities

The Metacognition System receives input from the Executive Function for monitoring purposes and accesses the Memory System for reflection. It provides oversight to the entire Cognitive Control System, informs the Learning System about process improvements, and provides confidence estimates to the Decision Making System.

This system forms a higher level of cognitive control, providing a supervisory function that monitors, evaluates, and regulates the cognitive architecture's operations. Through metacognition, the system can improve performance over time, adapt to new situations, and develop self-awareness of its own processing.'''
    },
    
    "cognitive-control/components/planning.md": {
        "title": "Planning System",
        "description": "This diagram details the planning component of the NeuroCognitive Architecture (NCA) cognitive control system.",
        "diagram_type": "graph TB",
        "class_defs": "classDef planning fill:#302010,stroke:#555,color:#fff\nclassDef process fill:#252525,stroke:#555,color:#fff",
        "diagram_content": '''subgraph PlanningSystem["Planning System"]
        direction TB
        class PlanningSystem main
        
        subgraph SequenceGeneration["Sequence Generation"]
            direction TB
            class SequenceGeneration planning
            ActionSequencing[Action<br>Sequencing] --- OperationOrdering[Operation<br>Ordering]
            StepIdentification[Step<br>Identification] --- PathConstruction[Path<br>Construction]
            class ActionSequencing,OperationOrdering,StepIdentification,PathConstruction subcomponent
        end
        
        subgraph StepPlanning["Step Planning"]
            direction TB
            class StepPlanning planning
            ActionSpecification[Action<br>Specification] --- StepParameters[Step<br>Parameters]
            ResourceAllocation[Resource<br>Allocation] --- StepConstraints[Step<br>Constraints]
            class ActionSpecification,StepParameters,ResourceAllocation,StepConstraints subcomponent
        end
        
        subgraph OutcomeForecasting["Outcome Forecasting"]
            direction TB
            class OutcomeForecasting planning
            ResultPrediction[Result<br>Prediction] --- StateProjection[State<br>Projection]
            ImpactAssessment[Impact<br>Assessment] --- FeedbackAnticipation[Feedback<br>Anticipation]
            class ResultPrediction,StateProjection,ImpactAssessment,FeedbackAnticipation subcomponent
        end
        
        subgraph AlternativeGeneration["Alternative Generation"]
            direction TB
            class AlternativeGeneration planning
            OptionGeneraton[Option<br>Generation] --- PlanVariants[Plan<br>Variants]
            ContingencyPlanning[Contingency<br>Planning] --- FallbackOptions[Fallback<br>Options]
            class OptionGeneraton,PlanVariants,ContingencyPlanning,FallbackOptions subcomponent
        end
        
        subgraph PlanOptimization["Plan Optimization"]
            direction TB
            class PlanOptimization planning
            EfficiencyAnalysis[Efficiency<br>Analysis] --- RedundancyElimination[Redundancy<br>Elimination]
            RiskMinimization[Risk<br>Minimization] --- ResourceOptimization[Resource<br>Optimization]
            class EfficiencyAnalysis,RedundancyElimination,RiskMinimization,ResourceOptimization subcomponent
        end
        
        subgraph PlanAdaptation["Plan Adaptation"]
            direction TB
            class PlanAdaptation planning
                        ReplanTrigger[Replan<br>Trigger] --- PlanModification[Plan<br>Modification]
            DynamicAdjustment[Dynamic<br>Adjustment] --- ContextualUpdate[Contextual<br>Update]
            class ReplanTrigger,PlanModification,DynamicAdjustment,ContextualUpdate subcomponent
        end
    end
    
    %% External connections
    GoalManager[Goal<br>Manager] --> SequenceGeneration
    DecisionMaker[Decision<br>Maker] --> AlternativeGeneration
    Metacognition[Metacognition] --> PlanOptimization
    
    %% Internal connections
    SequenceGeneration --> StepPlanning
    StepPlanning --> OutcomeForecasting
    OutcomeForecasting --> AlternativeGeneration
    AlternativeGeneration --> PlanOptimization
    PlanOptimization --> PlanAdaptation
    
    %% Feedback loops
    OutcomeForecasting --> SequenceGeneration
    PlanAdaptation --> SequenceGeneration
    
    %% Output connection
    PlanAdaptation --> ExecutionSystem[Execution<br>System]
    
    class GoalManager,DecisionMaker,Metacognition,ExecutionSystem subcomponent''',
        "section_title": "Planning System Components",
        "section_content": '''The Planning System is responsible for generating, evaluating, optimizing, and adapting plans to achieve goals. It includes the following key components:

### Sequence Generation
- **Action Sequencing**: Determines the order of actions in a plan
- **Operation Ordering**: Orders lower-level operations within actions
- **Step Identification**: Identifies the necessary steps to achieve a goal
- **Path Construction**: Builds the sequence of steps forming the plan

### Step Planning
- **Action Specification**: Defines the details of each action in the plan
- **Step Parameters**: Specifies parameters required for each step
- **Resource Allocation**: Assigns resources needed for each step
- **Step Constraints**: Defines constraints and conditions for each step

### Outcome Forecasting
- **Result Prediction**: Predicts the likely outcome of executing the plan
- **State Projection**: Forecasts the system state after plan execution
- **Impact Assessment**: Evaluates the potential impact of the plan
- **Feedback Anticipation**: Predicts expected feedback during execution

### Alternative Generation
- **Option Generation**: Creates alternative actions or steps
- **Plan Variants**: Develops different versions of the plan
- **Contingency Planning**: Creates backup plans for potential failures
- **Fallback Options**: Defines alternative actions if primary steps fail

### Plan Optimization
- **Efficiency Analysis**: Evaluates the efficiency of the plan
- **Redundancy Elimination**: Removes unnecessary steps or actions
- **Risk Minimization**: Modifies the plan to reduce potential risks
- **Resource Optimization**: Optimizes the use of resources in the plan

### Plan Adaptation
- **Replan Trigger**: Detects conditions requiring plan modification
- **Plan Modification**: Alters the plan based on new information or feedback
- **Dynamic Adjustment**: Makes real-time adjustments during execution
- **Contextual Update**: Updates the plan based on changes in the environment or context

The Planning System receives goals from the Goal Manager, uses the Decision Maker for evaluating alternatives, and is monitored by the Metacognition system for optimization. It produces plans for the Execution System.'''
    },

    # Memory System Components
    "memory-system/components/backends.md": {
        "title": "Memory Backends",
        "description": "Details of the storage backend implementations for the NCA memory system.",
        "diagram_type": "graph TB",
        "class_defs": "classDef backend fill:#302030,stroke:#555,color:#fff",
        "diagram_content": '''subgraph Backends["Storage Backends"]
        direction TB
        class Backends main
        
        BackendInterface[Backend<br>Interface]:::component
        
        subgraph InMemory["In-Memory Backend"]
            direction TB
            class InMemory backend
            RAMStore[RAM<br>Storage] --- DictStore[Dictionary<br>Store]
            Volatile[Volatile<br>Nature] --- FastAccess[Fast<br>Access]
            class RAMStore,DictStore,Volatile,FastAccess subcomponent
        end
        
        subgraph SQLite["SQLite Backend"]
            direction TB
            class SQLite backend
            FileDB[File-based<br>Database] --- SQLOps[SQL<br>Operations]
            SchemaMgmt[Schema<br>Management] --- Indexing[DB<br>Indexing]
            class FileDB,SQLOps,SchemaMgmt,Indexing subcomponent
        end
        
        subgraph Redis["Redis Backend"]
            direction TB
            class Redis backend
            KeyValue[Key-Value<br>Store] --- Caching[Caching<br>Layer]
            Persistence[Persistence<br>Options] --- DataStructures[Redis Data<br>Structures]
            class KeyValue,Caching,Persistence,DataStructures subcomponent
        end
        
        subgraph Vector["Vector Storage Backend"]
            direction TB
            class Vector backend
            VectorDB[Vector<br>Database<br>(e.g., LanceDB)] --- SimilaritySearch[Similarity<br>Search]
            EmbeddingStore[Embedding<br>Storage] --- Indexing[Vector<br>Indexing]
            class VectorDB,SimilaritySearch,EmbeddingStore,Indexing subcomponent
        end
    end
    
    %% Connections
    BackendInterface --> InMemory
    BackendInterface --> SQLite
    BackendInterface --> Redis
    BackendInterface --> Vector
    
    MemoryManager[Memory<br>Manager] --> BackendInterface
    
    class MemoryManager subcomponent''',
        "section_title": "Memory Backend Components",
        "section_content": '''The NCA memory system supports multiple storage backends, allowing flexibility in deployment and performance characteristics. All backends adhere to a common `BackendInterface`.

### In-Memory Backend
- **RAM Storage**: Stores data directly in system memory.
- **Dictionary Store**: Often implemented using Python dictionaries.
- **Volatile Nature**: Data is lost when the system restarts unless persistence is separately managed.
- **Fast Access**: Provides the fastest access speeds. Suitable for Working Memory.

### SQLite Backend
- **File-based Database**: Stores data in a local file.
- **SQL Operations**: Uses standard SQL for data manipulation.
- **Schema Management**: Defines table structures for memory items.
- **DB Indexing**: Uses database indexes for faster querying. Suitable for persistent storage on single nodes.

### Redis Backend
- **Key-Value Store**: Stores data primarily as key-value pairs.
- **Caching Layer**: Can be used as a fast cache in front of other backends.
- **Persistence Options**: Offers configurable persistence mechanisms (RDB, AOF).
- **Redis Data Structures**: Leverages Redis's advanced data structures (hashes, lists, sets). Suitable for distributed caching or session storage.

### Vector Storage Backend
- **Vector Database**: Specialized database for storing and querying high-dimensional vectors (e.g., LanceDB, Milvus, Pinecone).
- **Similarity Search**: Enables efficient searching based on vector similarity (e.g., cosine similarity, dot product).
- **Embedding Storage**: Stores vector embeddings generated from memory content.
- **Vector Indexing**: Uses specialized indexing techniques (e.g., HNSW, IVF) for fast vector search. Crucial for Semantic Memory retrieval based on meaning.'''
    },

    "memory-system/components/lymphatic.md": {
        "title": "Lymphatic System",
        "description": "Details of the Lymphatic System responsible for memory maintenance and cleaning.",
        "diagram_type": "graph TB",
        "class_defs": "classDef lymphatic fill:#203020,stroke:#555,color:#fff",
        "diagram_content": '''subgraph LymphaticSystem["Lymphatic System"]
        direction TB
        class LymphaticSystem main
        
        Scheduler[Maintenance<br>Scheduler]:::component
        
        subgraph Cleaning["Memory Cleaning"]
            direction TB
            class Cleaning lymphatic
            ObsoleteDetection[Obsolete<br>Detection] --- RedundancyCheck[Redundancy<br>Check]
            IrrelevanceMarking[Irrelevance<br>Marking] --- DecayApplication[Decay<br>Application]
            class ObsoleteDetection,RedundancyCheck,IrrelevanceMarking,DecayApplication subcomponent
        end
        
        subgraph Pruning["Memory Pruning"]
            direction TB
            class Pruning lymphatic
            WeakLinkRemoval[Weak Link<br>Removal] --- LowImportance[Low Importance<br>Removal]
            AgeBasedPruning[Age-Based<br>Pruning] --- CapacityMgmt[Capacity<br>Management]
            class WeakLinkRemoval,LowImportance,AgeBasedPruning,CapacityMgmt subcomponent
        end
        
        subgraph Maintenance["Health Maintenance"]
            direction TB
            class Maintenance lymphatic
            IntegrityCheck[Integrity<br>Check] --- ConsistencyCheck[Consistency<br>Check]
            IndexRebuild[Index<br>Rebuild] --- StatUpdate[Statistics<br>Update]
            class IntegrityCheck,ConsistencyCheck,IndexRebuild,StatUpdate subcomponent
        end
        
        subgraph Repair["Memory Repair"]
            direction TB
            class Repair lymphatic
            CorruptionDetection[Corruption<br>Detection] --- DataRecovery[Data<br>Recovery]
            LinkReconstruction[Link<br>Reconstruction] --- ErrorCorrection[Error<br>Correction]
            class CorruptionDetection,DataRecovery,LinkReconstruction,ErrorCorrection subcomponent
        end
    end
    
    %% Connections
    Scheduler --> Cleaning
    Scheduler --> Pruning
    Scheduler --> Maintenance
    Scheduler --> Repair
    
    MemoryManager[Memory<br>Manager] --> Scheduler
    HealthSystem[Health<br>System] --> Scheduler
    
    Cleaning --> Pruning
    Maintenance --> Repair
    
    class MemoryManager,HealthSystem subcomponent''',
        "section_title": "Lymphatic System Components",
        "section_content": '''Inspired by the brain's glymphatic system, the NCA's Lymphatic System performs background maintenance tasks to keep the memory system healthy and efficient.

### Maintenance Scheduler
- Orchestrates the execution of cleaning, pruning, maintenance, and repair tasks, often during periods of low cognitive load (simulated "sleep").

### Memory Cleaning
- **Obsolete Detection**: Identifies memory items that are no longer valid or relevant.
- **Redundancy Check**: Finds and marks duplicate or redundant information.
- **Irrelevance Marking**: Flags items that have become irrelevant based on current goals or context.
- **Decay Application**: Applies decay mechanisms to reduce the strength or salience of unused items.

### Memory Pruning
- **Weak Link Removal**: Removes weak connections between memory items.
- **Low Importance Removal**: Deletes items deemed unimportant based on metadata or usage.
- **Age-Based Pruning**: Removes old items that haven't been accessed recently (configurable).
- **Capacity Management**: Prunes items to stay within storage capacity limits.

### Health Maintenance
- **Integrity Check**: Verifies the structural integrity of memory data.
- **Consistency Check**: Ensures consistency across related memory items and indexes.
- **Index Rebuild**: Rebuilds search indexes for optimal performance.
- **Statistics Update**: Updates metadata and statistics about memory usage.

### Memory Repair
- **Corruption Detection**: Identifies corrupted or damaged memory data.
- **Data Recovery**: Attempts to recover data from backups or redundant sources.
- **Link Reconstruction**: Tries to repair broken links between memory items.
- **Error Correction**: Corrects errors in memory content where possible.

The Lymphatic System is triggered by the Memory Manager, potentially influenced by the Health System's state (e.g., running more intensively during low-load periods). Its goal is to prevent memory clutter, maintain performance, and ensure data integrity.'''
    },
    
    # ... (Add definitions for annealing.md, tubules.md, manager.md for memory system) ...
    # ... (Add definitions for monitoring.md, dynamics.md, registry.md, metrics.md, alerting.md for health system) ...
    # ... (Add definitions for overview.md, llm.md, apis.md, plugins.md, data-exchange.md for integration) ...
    # ... (Add definitions for data-flow/index.md, events/index.md, infrastructure/index.md) ...
}

def generate_diagram_file(filepath, data):
    """Generates a single diagram Markdown file."""
    full_path = DOCS_DIR / filepath
    ensure_dir(full_path.parent)
    
    try:
        # Format the Mermaid diagram
        diagram = MERMAID_TEMPLATE.format(
            diagram_type=data.get("diagram_type", "graph TB"),
            class_defs=data.get("class_defs", ""),
            diagram_content=data.get("diagram_content", "    A[Missing Diagram Content]")
        )
        
        # Format the full Markdown content
        content = MARKDOWN_TEMPLATE.format(
            title=data.get("title", "Untitled Diagram"),
            description=data.get("description", ""),
            diagram=diagram,
            section_title=data.get("section_title", "Components"),
            section_content=data.get("section_content", "No details provided.")
        )
        
        # Write the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated: {full_path}")
        
    except KeyError as e:
        print(f"Error generating {full_path}: Missing key {e} in COMPONENTS dictionary.", file=sys.stderr)
    except Exception as e:
        print(f"Error generating {full_path}: {e}", file=sys.stderr)

def main():
    """Main function to generate all diagram files."""
    print(f"Generating diagrams in: {DOCS_DIR.resolve()}")
    
    # Ensure base diagrams directory exists
    ensure_dir(DOCS_DIR)
    
    # Generate each file
    for filepath, data in COMPONENTS.items():
        generate_diagram_file(filepath, data)
        
    print("Diagram generation complete.")

if __name__ == "__main__":
    # Change working directory if script is not run from the project root
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent.resolve() # Assumes script is in Neuroca/scripts
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
    
    main()
