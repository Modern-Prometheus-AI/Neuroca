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
    
    # Health System Components
    "health-system/components/monitoring.md": {
        "title": "Health Monitoring System",
        "description": "Details of the health monitoring system in the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef monitoring fill:#203040,stroke:#555,color:#fff",
        "diagram_content": '''subgraph HealthMonitoring["Health Monitoring System"]
        direction TB
        class HealthMonitoring main
        
        subgraph MetricsCollection["Metrics Collection"]
            direction TB
            class MetricsCollection monitoring
            ResourceMetrics[Resource<br>Metrics] --- PerformanceMetrics[Performance<br>Metrics]
            SystemMetrics[System<br>Metrics] --- ComponentMetrics[Component<br>Metrics]
            class ResourceMetrics,PerformanceMetrics,SystemMetrics,ComponentMetrics subcomponent
        end
        
        subgraph HealthAnalysis["Health Analysis"]
            direction TB
            class HealthAnalysis monitoring
            ThresholdAnalysis[Threshold<br>Analysis] --- AnomalyDetection[Anomaly<br>Detection]
            TrendAnalysis[Trend<br>Analysis] --- PatternRecognition[Pattern<br>Recognition]
            class ThresholdAnalysis,AnomalyDetection,TrendAnalysis,PatternRecognition subcomponent
        end
        
        subgraph AlertSystem["Alert System"]
            direction TB
            class AlertSystem monitoring
            AlertGeneration[Alert<br>Generation] --- AlertRouting[Alert<br>Routing]
            AlertPrioritization[Alert<br>Prioritization] --- AlertSuppression[Alert<br>Suppression]
            class AlertGeneration,AlertRouting,AlertPrioritization,AlertSuppression subcomponent
        end
        
        subgraph HealthReporting["Health Reporting"]
            direction TB
            class HealthReporting monitoring
            DashboardReporting[Dashboard<br>Reporting] --- LogReporting[Log<br>Reporting]
            MetricVisualization[Metric<br>Visualization] --- HealthSummary[Health<br>Summary]
            class DashboardReporting,LogReporting,MetricVisualization,HealthSummary subcomponent
        end
        
        subgraph HealthProbes["Health Probes"]
            direction TB
            class HealthProbes monitoring
            ActiveProbes[Active<br>Probes] --- PassiveProbes[Passive<br>Probes]
            PeriodicChecks[Periodic<br>Checks] --- OnDemandChecks[On-Demand<br>Checks]
            class ActiveProbes,PassiveProbes,PeriodicChecks,OnDemandChecks subcomponent
        end
    end
    
    %% External connections
    ComponentRegistry[Component<br>Registry] --> HealthProbes
    HealthSystem[Health<br>System] --> MetricsCollection
    
    %% Internal connections
    HealthProbes --> MetricsCollection
    MetricsCollection --> HealthAnalysis
    HealthAnalysis --> AlertSystem
    HealthAnalysis --> HealthReporting
    
    %% Outputs
    AlertSystem --> NotificationSystem[Notification<br>System]
    HealthReporting --> Dashboard[Health<br>Dashboard]
    
    class ComponentRegistry,HealthSystem,NotificationSystem,Dashboard subcomponent''',
        "section_title": "Health Monitoring System Components",
        "section_content": '''The Health Monitoring System is responsible for collecting, analyzing, and reporting on the health of the NeuroCognitive Architecture.

### Metrics Collection
- **Resource Metrics**: Collects metrics related to system resources (CPU, memory, storage)
- **Performance Metrics**: Gathers metrics on system performance and response times
- **System Metrics**: Collects overall system state and operation metrics
- **Component Metrics**: Gathers metrics specific to individual components

### Health Analysis
- **Threshold Analysis**: Compares metrics against predefined thresholds
- **Anomaly Detection**: Identifies unusual patterns or deviations from normal behavior
- **Trend Analysis**: Analyzes changes in metrics over time
- **Pattern Recognition**: Identifies known patterns that may indicate issues

### Alert System
- **Alert Generation**: Creates alerts when issues are detected
- **Alert Routing**: Routes alerts to appropriate handlers
- **Alert Prioritization**: Assigns priority levels to alerts
- **Alert Suppression**: Prevents duplicate or unnecessary alerts

### Health Reporting
- **Dashboard Reporting**: Presents health data in visual dashboards
- **Log Reporting**: Records health events and issues in logs
- **Metric Visualization**: Creates visual representations of health metrics
- **Health Summary**: Generates summaries of system health status

### Health Probes
- **Active Probes**: Actively test system components
- **Passive Probes**: Collect data without interfering with operation
- **Periodic Checks**: Regularly scheduled health checks
- **On-Demand Checks**: Health checks triggered by specific events

The Health Monitoring System integrates with the Component Registry to discover components to monitor and with the Health System to provide data for regulation decisions. It outputs alerts to the Notification System and provides visualizations and summaries to the Health Dashboard.'''
    },
    
    "health-system/components/dynamics.md": {
        "title": "Health Dynamics System",
        "description": "Details of the health dynamics system in the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef dynamics fill:#203020,stroke:#555,color:#fff",
        "diagram_content": '''subgraph HealthDynamics["Health Dynamics System"]
        direction TB
        class HealthDynamics main
        
        subgraph StateManagement["State Management"]
            direction TB
            class StateManagement dynamics
            StateRepresentation[State<br>Representation] --- StateTransitions[State<br>Transitions]
            StateHistory[State<br>History] --- StatePrediction[State<br>Prediction]
            class StateRepresentation,StateTransitions,StateHistory,StatePrediction subcomponent
        end
        
        subgraph Degradation["Health Degradation"]
            direction TB
            class Degradation dynamics
            FatigueModels[Fatigue<br>Models] --- StressModels[Stress<br>Models]
            LoadModels[Load<br>Models] --- AgingModels[Aging<br>Models]
            class FatigueModels,StressModels,LoadModels,AgingModels subcomponent
        end
        
        subgraph Recovery["Health Recovery"]
            direction TB
            class Recovery dynamics
            RestMechanisms[Rest<br>Mechanisms] --- RepairProcesses[Repair<br>Processes]
            OptimizationMechanisms[Optimization<br>Mechanisms] --- RejuvenationProcesses[Rejuvenation<br>Processes]
            class RestMechanisms,RepairProcesses,OptimizationMechanisms,RejuvenationProcesses subcomponent
        end
        
        subgraph Regulation["Health Regulation"]
            direction TB
            class Regulation dynamics
            ResourceAllocation[Resource<br>Allocation] --- LoadBalancing[Load<br>Balancing]
            PriorityAdjustment[Priority<br>Adjustment] --- ComponentThrottling[Component<br>Throttling]
            class ResourceAllocation,LoadBalancing,PriorityAdjustment,ComponentThrottling subcomponent
        end
        
        subgraph Homeostasis["Homeostasis System"]
            direction TB
            class Homeostasis dynamics
            SetPointManagement[Set Point<br>Management] --- FeedbackLoops[Feedback<br>Loops]
            EquilibriumSeeking[Equilibrium<br>Seeking] --- StabilityMechanisms[Stability<br>Mechanisms]
            class SetPointManagement,FeedbackLoops,EquilibriumSeeking,StabilityMechanisms subcomponent
        end
    end
    
    %% External connections
    HealthMonitor[Health<br>Monitor] --> StateManagement
    MemorySystem[Memory<br>System] --- Degradation
    CognitiveSystem[Cognitive<br>System] --- Recovery
    
    %% Internal connections
    StateManagement --> Degradation
    StateManagement --> Recovery
    Degradation --> Regulation
    Recovery --> Regulation
    Regulation --> Homeostasis
    Homeostasis --> StateManagement
    
    %% Outputs
    Regulation --> ResourceController[Resource<br>Controller]
    Regulation --> ProcessScheduler[Process<br>Scheduler]
    
    class HealthMonitor,MemorySystem,CognitiveSystem,ResourceController,ProcessScheduler subcomponent''',
        "section_title": "Health Dynamics System Components",
        "section_content": '''The Health Dynamics System models and regulates the operational health of the NeuroCognitive Architecture using mechanisms inspired by biological homeostasis.

### State Management
- **State Representation**: Models the current health state of the system
- **State Transitions**: Manages transitions between different health states
- **State History**: Maintains a history of past health states
- **State Prediction**: Predicts future health states based on current trends

### Health Degradation
- **Fatigue Models**: Simulates system fatigue under continuous operation
- **Stress Models**: Models the impact of high load or pressure on system health
- **Load Models**: Represents the relationship between load and system health
- **Aging Models**: Simulates longer-term degradation of system capabilities

### Health Recovery
- **Rest Mechanisms**: Simulates recovery during periods of low activity
- **Repair Processes**: Models self-repair capabilities of the system
- **Optimization Mechanisms**: Represents efficiency improvements after recovery
- **Rejuvenation Processes**: Simulates periodic deep recovery processes

### Health Regulation
- **Resource Allocation**: Adjusts resource allocation based on health state
- **Load Balancing**: Redistributes load to maintain system health
- **Priority Adjustment**: Modifies task priorities based on health considerations
- **Component Throttling**: Reduces activity of overloaded components

### Homeostasis System
- **Set Point Management**: Maintains optimal health parameters
- **Feedback Loops**: Implements negative feedback to maintain stability
- **Equilibrium Seeking**: Works to return the system to a balanced state
- **Stability Mechanisms**: Prevents oscillations and instability

The Health Dynamics System receives health state information from the Health Monitor and interacts with the Memory and Cognitive Systems to model their health degradation and recovery. It outputs control signals to the Resource Controller and Process Scheduler to regulate system operation.'''
    },
    
    "health-system/components/registry.md": {
        "title": "Health Component Registry",
        "description": "Details of the health component registry in the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef registry fill:#302030,stroke:#555,color:#fff",
        "diagram_content": '''subgraph ComponentRegistry["Health Component Registry"]
        direction TB
        class ComponentRegistry main
        
        subgraph Registration["Component Registration"]
            direction TB
            class Registration registry
            RegisterComponent[Register<br>Component] --- UnregisterComponent[Unregister<br>Component]
            UpdateComponent[Update<br>Component] --- ComponentLifecycle[Component<br>Lifecycle]
            class RegisterComponent,UnregisterComponent,UpdateComponent,ComponentLifecycle subcomponent
        end
        
        subgraph Discovery["Component Discovery"]
            direction TB
            class Discovery registry
            AutoDiscovery[Auto<br>Discovery] --- ManualDiscovery[Manual<br>Discovery]
            ServiceDiscovery[Service<br>Discovery] --- ComponentScan[Component<br>Scan]
            class AutoDiscovery,ManualDiscovery,ServiceDiscovery,ComponentScan subcomponent
        end
        
        subgraph ComponentStore["Component Store"]
            direction TB
            class ComponentStore registry
            ComponentDatabase[Component<br>Database] --- ComponentCache[Component<br>Cache]
            RelationshipStore[Relationship<br>Store] --- MetadataStore[Metadata<br>Store]
            class ComponentDatabase,ComponentCache,RelationshipStore,MetadataStore subcomponent
        end
        
        subgraph Query["Component Query"]
            direction TB
            class Query registry
            QueryByType[Query By<br>Type] --- QueryByName[Query By<br>Name]
            QueryByHealth[Query By<br>Health] --- QueryByRelationship[Query By<br>Relationship]
            class QueryByType,QueryByName,QueryByHealth,QueryByRelationship subcomponent
        end
        
        subgraph Dependency["Dependency Management"]
            direction TB
            class Dependency registry
            DependencyTracking[Dependency<br>Tracking] --- DependencyResolution[Dependency<br>Resolution]
            DependencyVerification[Dependency<br>Verification] --- DependencyNotification[Dependency<br>Notification]
            class DependencyTracking,DependencyResolution,DependencyVerification,DependencyNotification subcomponent
        end
    end
    
    %% External connections
    SystemComponents[System<br>Components] --> Registration
    HealthMonitor[Health<br>Monitor] --> ComponentStore
    
    %% Internal connections
    Registration --> ComponentStore
    Discovery --> Registration
    ComponentStore --> Query
    ComponentStore --> Dependency
    
    %% Outputs
    ComponentStore --> HealthProbes[Health<br>Probes]
    Query --> HealthAnalysis[Health<br>Analysis]
    
    class SystemComponents,HealthMonitor,HealthProbes,HealthAnalysis subcomponent''',
        "section_title": "Health Component Registry Components",
        "section_content": '''The Health Component Registry manages the registration, discovery, and tracking of components within the NeuroCognitive Architecture that participate in the health system.

### Component Registration
- **Register Component**: Adds components to the health system
- **Unregister Component**: Removes components from the health system
- **Update Component**: Updates component information
- **Component Lifecycle**: Manages component lifecycle events

### Component Discovery
- **Auto Discovery**: Automatically discovers eligible components
- **Manual Discovery**: Allows manual addition of components
- **Service Discovery**: Discovers components via service discovery mechanisms
- **Component Scan**: Scans the system for eligible components

### Component Store
- **Component Database**: Persistent storage for component information
- **Component Cache**: In-memory cache for faster access
- **Relationship Store**: Stores relationships between components
- **Metadata Store**: Stores health-related metadata for components

### Component Query
- **Query By Type**: Finds components by their type
- **Query By Name**: Retrieves components by name
- **Query By Health**: Queries components by health status
- **Query By Relationship**: Finds components based on their relationships

### Dependency Management
- **Dependency Tracking**: Tracks dependencies between components
- **Dependency Resolution**: Resolves dependency references
- **Dependency Verification**: Verifies dependency health and availability
- **Dependency Notification**: Notifies components of dependency changes

The Component Registry interacts with all System Components for registration, and with the Health Monitor for health status updates. It provides component information to Health Probes for monitoring and to Health Analysis for context-aware analysis.'''
    },

    # Integration Components
    "integration/components/llm.md": {
        "title": "LLM Integration System",
        "description": "Details of the LLM integration system in the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef llm fill:#203040,stroke:#555,color:#fff",
        "diagram_content": '''subgraph LLMIntegration["LLM Integration System"]
        direction TB
        class LLMIntegration main
        
        subgraph Connectors["LLM Connectors"]
            direction TB
            class Connectors llm
            OpenAIConnector[OpenAI<br>Connector] --- AnthropicConnector[Anthropic<br>Connector]
            HuggingFaceConnector[HuggingFace<br>Connector] --- LocalLLMConnector[Local LLM<br>Connector]
            class OpenAIConnector,AnthropicConnector,HuggingFaceConnector,LocalLLMConnector subcomponent
        end
        
        subgraph ModelManagement["Model Management"]
            direction TB
            class ModelManagement llm
            ModelSelection[Model<br>Selection] --- ModelVersioning[Model<br>Versioning]
            ModelCaching[Model<br>Caching] --- ModelFallback[Model<br>Fallback]
            class ModelSelection,ModelVersioning,ModelCaching,ModelFallback subcomponent
        end
        
        subgraph PromptEngineering["Prompt Engineering"]
            direction TB
            class PromptEngineering llm
            PromptTemplates[Prompt<br>Templates] --- PromptChaining[Prompt<br>Chaining]
            FewShotExamples[Few-Shot<br>Examples] --- PromptOptimization[Prompt<br>Optimization]
            class PromptTemplates,PromptChaining,FewShotExamples,PromptOptimization subcomponent
        end
        
        subgraph Embeddings["Embedding System"]
            direction TB
            class Embeddings llm
            TextEmbedding[Text<br>Embedding] --- ContentEmbedding[Content<br>Embedding]
            EmbeddingStorage[Embedding<br>Storage] --- EmbeddingRetrieval[Embedding<br>Retrieval]
            class TextEmbedding,ContentEmbedding,EmbeddingStorage,EmbeddingRetrieval subcomponent
        end
        
        subgraph ResponseProcessing["Response Processing"]
            direction TB
            class ResponseProcessing llm
            ResponseParsing[Response<br>Parsing] --- ResponseValidation[Response<br>Validation]
            ErrorHandling[Error<br>Handling] --- Formatting[Response<br>Formatting]
            class ResponseParsing,ResponseValidation,ErrorHandling,Formatting subcomponent
        end
    end
    
    %% External connections
    ExternalLLMs[External<br>LLMs] --> Connectors
    MemorySystem[Memory<br>System] <--> Embeddings
    
    %% Internal connections
    Connectors --> ModelManagement
    ModelManagement --> PromptEngineering
    PromptEngineering --> ResponseProcessing
    Embeddings --> PromptEngineering
    
    %% Outputs
    ResponseProcessing --> CognitiveSystem[Cognitive<br>System]
    Embeddings --> SemanticMemory[Semantic<br>Memory]
    
    class ExternalLLMs,MemorySystem,CognitiveSystem,SemanticMemory subcomponent''',
        "section_title": "LLM Integration System Components",
        "section_content": '''The LLM Integration System connects the NeuroCognitive Architecture with external Large Language Models, enabling semantic understanding and generation capabilities.

### LLM Connectors
- **OpenAI Connector**: Interfaces with OpenAI models (GPT-4, etc.)
- **Anthropic Connector**: Interfaces with Anthropic models (Claude, etc.)
- **HuggingFace Connector**: Connects to models hosted on HuggingFace
- **Local LLM Connector**: Interfaces with locally deployed LLMs

### Model Management
- **Model Selection**: Chooses appropriate models based on task requirements
- **Model Versioning**: Manages different versions of models
- **Model Caching**: Caches model results for efficiency
- **Model Fallback**: Provides fallback options when primary models fail

### Prompt Engineering
- **Prompt Templates**: Manages templates for different prompt types
- **Prompt Chaining**: Chains multiple prompts for complex tasks
- **Few-Shot Examples**: Provides examples for in-context learning
- **Prompt Optimization**: Optimizes prompts for better performance

### Embedding System
- **Text Embedding**: Converts text to vector embeddings
- **Content Embedding**: Embeds various content types (images, etc.)
- **Embedding Storage**: Stores embeddings for retrieval
- **Embedding Retrieval**: Retrieves embeddings for similarity search

### Response Processing
- **Response Parsing**: Parses structured data from LLM responses
- **Response Validation**: Validates responses against expected formats
- **Error Handling**: Manages errors in LLM interactions
- **Response Formatting**: Formats responses for downstream use

The LLM Integration System connects to External LLMs through the Connectors module and interacts bidirectionally with the Memory System, particularly for embedding storage and retrieval. It provides processed responses to the Cognitive System and sends embeddings to the Semantic Memory component.'''
    },
    
    "integration/components/apis.md": {
        "title": "API Integration System",
        "description": "Details of the API integration system in the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef api fill:#302030,stroke:#555,color:#fff",
        "diagram_content": '''subgraph APIIntegration["API Integration System"]
        direction TB
        class APIIntegration main
        
        subgraph RESTfulAPI["RESTful API"]
            direction TB
            class RESTfulAPI api
            Endpoints[API<br>Endpoints] --- Controllers[API<br>Controllers]
            RequestHandling[Request<br>Handling] --- ResponseFormatting[Response<br>Formatting]
            class Endpoints,Controllers,RequestHandling,ResponseFormatting subcomponent
        end
        
        subgraph GraphQLAPI["GraphQL API"]
            direction TB
            class GraphQLAPI api
            Schema[GraphQL<br>Schema] --- Resolvers[GraphQL<br>Resolvers]
            QueryHandling[Query<br>Handling] --- MutationHandling[Mutation<br>Handling]
            class Schema,Resolvers,QueryHandling,MutationHandling subcomponent
        end
        
        subgraph Authentication["Authentication System"]
            direction TB
            class Authentication api
            AuthMethods[Auth<br>Methods] --- TokenManagement[Token<br>Management]
            IdentityVerification[Identity<br>Verification] --- SessionManagement[Session<br>Management]
            class AuthMethods,TokenManagement,IdentityVerification,SessionManagement subcomponent
        end
        
        subgraph Authorization["Authorization System"]
            direction TB
            class Authorization api
            RoleManagement[Role<br>Management] --- PermissionChecking[Permission<br>Checking]
            AccessControl[Access<br>Control] --- PolicyEnforcement[Policy<br>Enforcement]
            class RoleManagement,PermissionChecking,AccessControl,PolicyEnforcement subcomponent
        end
        
        subgraph APIGateway["API Gateway"]
            direction TB
            class APIGateway api
            RequestRouting[Request<br>Routing] --- RateLimiting[Rate<br>Limiting]
            LoadBalancing[Load<br>Balancing] --- Caching[Response<br>Caching]
            class RequestRouting,RateLimiting,LoadBalancing,Caching subcomponent
        end
    end
    
    %% External connections
    ExternalClients[External<br>Clients] --> APIGateway
    InternalSystems[Internal<br>Systems] <--> RESTfulAPI
    InternalSystems <--> GraphQLAPI
    
    %% Internal connections
    APIGateway --> RESTfulAPI
    APIGateway --> GraphQLAPI
    Authentication --> RESTfulAPI
    Authentication --> GraphQLAPI
    Authorization --> RESTfulAPI
    Authorization --> GraphQLAPI
    
    %% Outputs
    RESTfulAPI --> MemorySystem[Memory<br>System]
    GraphQLAPI --> CognitiveSystem[Cognitive<br>System]
    
    class ExternalClients,InternalSystems,MemorySystem,CognitiveSystem subcomponent''',
        "section_title": "API Integration System Components",
        "section_content": '''The API Integration System provides interfaces for external systems to interact with the NeuroCognitive Architecture through standardized APIs.

### RESTful API
- **API Endpoints**: Defines URL endpoints for different operations
- **API Controllers**: Handles API requests and orchestrates responses
- **Request Handling**: Processes incoming API requests
- **Response Formatting**: Formats API responses according to standards

### GraphQL API
- **GraphQL Schema**: Defines the schema for GraphQL queries and mutations
- **GraphQL Resolvers**: Resolves GraphQL queries to data sources
- **Query Handling**: Processes GraphQL queries
- **Mutation Handling**: Handles GraphQL mutations (data changes)

### Authentication System
- **Auth Methods**: Supports multiple authentication methods
- **Token Management**: Manages authentication tokens
- **Identity Verification**: Verifies the identity of API users
- **Session Management**: Manages user sessions

### Authorization System
- **Role Management**: Manages user roles and permissions
- **Permission Checking**: Checks user permissions for operations
- **Access Control**: Controls access to protected resources
- **Policy Enforcement**: Enforces security policies

### API Gateway
- **Request Routing**: Routes requests to appropriate handlers
- **Rate Limiting**: Limits request rates to prevent abuse
- **Load Balancing**: Distributes load across multiple instances
- **Response Caching**: Caches responses for improved performance

The API Integration System serves as the interface between External Clients and the NeuroCognitive Architecture's Internal Systems. It provides both RESTful and GraphQL interfaces, with Authentication and Authorization systems ensuring secure access. The API Gateway manages incoming requests, applying rate limiting and load balancing for scalability.'''
    },
    
    # Additional infrastructure components
    "infrastructure/index.md": {
        "title": "Infrastructure Architecture",
        "description": "Overview of the infrastructure architecture for the NeuroCognitive Architecture.",
        "diagram_type": "graph TB",
        "class_defs": "classDef infra fill:#203020,stroke:#555,color:#fff",
        "diagram_content": '''subgraph Infrastructure["NCA Infrastructure"]
        direction TB
        class Infrastructure main
        
        subgraph Deployment["Deployment Architecture"]
            direction TB
            class Deployment infra
            ContainerOrchestration[Container<br>Orchestration] --- ServiceMesh[Service<br>Mesh]
            ConfigManagement[Configuration<br>Management] --- Scalability[Scalability<br>Systems]
            class ContainerOrchestration,ServiceMesh,ConfigManagement,Scalability subcomponent
        end
        
        subgraph Monitoring["Monitoring Infrastructure"]
            direction TB
            class Monitoring infra
            Logging[Logging<br>System] --- Metrics[Metrics<br>Collection]
            Tracing[Distributed<br>Tracing] --- Alerting[Alerting<br>System]
            class Logging,Metrics,Tracing,Alerting subcomponent
        end
        
        subgraph Storage["Storage Infrastructure"]
            direction TB
            class Storage infra
            DatabaseSystems[Database<br>Systems] --- ObjectStorage[Object<br>Storage]
            FileSystem[File<br>System] --- CacheLayer[Cache<br>Layer]
            class DatabaseSystems,ObjectStorage,FileSystem,CacheLayer subcomponent
        end
        
        subgraph Networking["Networking Infrastructure"]
            direction TB
            class Networking infra
            LoadBalancers[Load<br>Balancers] --- ServiceDiscovery[Service<br>Discovery]
            API[API<br>Gateway] --- Firewall[Security<br>Firewall]
            class LoadBalancers,ServiceDiscovery,API,Firewall subcomponent
        end
        
        subgraph Security["Security Infrastructure"]
            direction TB
            class Security infra
            Authentication[Authentication] --- Authorization[Authorization]
            Encryption[Encryption] --- Auditing[Security<br>Auditing]
            class Authentication,Authorization,Encryption,Auditing subcomponent
        end
    end
    
    %% High-level connections
    ExternalSystems[External<br>Systems] --> Networking
    DeveloperTools[Developer<br>Tools] --> Deployment
    
    %% Internal connections
    Networking --> Deployment
    Deployment --> Storage
    Monitoring --> Security
    Security --> Networking
    
    %% System connections
    NCACoreComponents[NCA Core<br>Components] --> Deployment
    Monitoring --> NCACoreComponents
    
    class ExternalSystems,DeveloperTools,NCACoreComponents subcomponent''',
        "section_title": "Infrastructure Architecture Components",
        "section_content": '''The Infrastructure Architecture provides the foundation for deploying, running, and managing the NeuroCognitive Architecture system.

### Deployment Architecture
- **Container Orchestration**: Manages containerized deployment (e.g., Kubernetes)
- **Service Mesh**: Handles service-to-service communication
- **Configuration Management**: Manages system configuration across environments
- **Scalability Systems**: Enables horizontal and vertical scaling of components

### Monitoring Infrastructure
- **Logging System**: Collects and manages system logs
- **Metrics Collection**: Gathers performance and operational metrics
- **Distributed Tracing**: Traces requests across distributed components
- **Alerting System**: Generates alerts on system issues

### Storage Infrastructure
- **Database Systems**: Manages structured data storage
- **Object Storage**: Stores unstructured objects (like embeddings)
- **File System**: Handles file-based storage
- **Cache Layer**: Provides caching for improved performance

### Networking Infrastructure
- **Load Balancers**: Distributes traffic across instances
- **Service Discovery**: Enables components to find each other
- **API Gateway**: Manages external API access
- **Security Firewall**: Protects against network threats

### Security Infrastructure
- **Authentication**: Verifies user identities
- **Authorization**: Controls access to resources
- **Encryption**: Protects data in transit and at rest
- **Security Auditing**: Records security-relevant events

The Infrastructure Architecture serves as the foundation upon which the NCA Core Components run. It interfaces with External Systems through the Networking layer and with Developer Tools through the Deployment layer. The architecture is designed to be scalable, resilient, and secure, providing the necessary infrastructure services for the cognitive architecture components.'''
    },
    
    "data-flow/index.md": {
        "title": "Data Flow Architecture",
        "description": "Overview of data flows in the NeuroCognitive Architecture.",
        "diagram_type": "graph LR",
        "class_defs": "classDef flow fill:#302030,stroke:#555,color:#fff",
        "diagram_content": '''subgraph DataFlow["NCA Data Flow"]
        direction TB
        class DataFlow main
        
        Input[External<br>Input]:::flow --> APILayer[API<br>Layer]:::flow
        APILayer --> InputProcessing[Input<br>Processing]:::flow
        InputProcessing --> MemorySystem[Memory<br>System]:::flow
        
        MemorySystem --> CognitiveSystem[Cognitive<br>System]:::flow
        CognitiveSystem --> ReasoningEngine[Reasoning<br>Engine]:::flow
        ReasoningEngine --> DecisionMaking[Decision<br>Making]:::flow
        
        DecisionMaking --> ActionSelection[Action<br>Selection]:::flow
        ActionSelection --> OutputFormation[Output<br>Formation]:::flow
        OutputFormation --> APILayer
        APILayer --> Output[External<br>Output]:::flow
        
        %% Memory Flows
        MemorySystem --> WorkingMemory[Working<br>Memory]:::flow
        MemorySystem --> EpisodicMemory[Episodic<br>Memory]:::flow
        MemorySystem --> SemanticMemory[Semantic<br>Memory]:::flow
        
        %% LLM Integration Flows
        InputProcessing --> LLMIntegration[LLM<br>Integration]:::flow
        LLMIntegration --> SemanticMemory
        LLMIntegration --> CognitiveSystem
        
        %% Health System Flows
        HealthSystem[Health<br>System]:::flow --> CognitiveSystem
        HealthSystem --> MemorySystem
        CognitiveSystem --> HealthSystem
        
        class WorkingMemory,EpisodicMemory,SemanticMemory,LLMIntegration,HealthSystem flow
    end''',
        "section_title": "Data Flow Architecture Components",
        "section_content": '''The Data Flow Architecture shows how information moves through the NeuroCognitive Architecture system, from input to output.

### Main Data Flow
- **External Input**: Information entering the system from external sources
- **API Layer**: Entry and exit point for external interactions
- **Input Processing**: Initial processing of incoming information
- **Memory System**: Storage and retrieval of information in the three-tiered memory
- **Cognitive System**: Core cognitive processing components
- **Reasoning Engine**: Applies reasoning methods to information
- **Decision Making**: Makes decisions based on reasoning and goals
- **Action Selection**: Selects actions based on decisions
- **Output Formation**: Formats the selected actions for output
- **External Output**: Information leaving the system to external recipients

### Memory Flows
- Information flows between the Memory System and its three tiers: Working Memory, Episodic Memory, and Semantic Memory
- Each tier has different storage characteristics and retrieval patterns

### LLM Integration Flows
- The LLM Integration component receives processed input
- It provides processed information to both the Semantic Memory and Cognitive System
- This enables embeddings for memory storage and semantic understanding for reasoning

### Health System Flows
- The Health System monitors and regulates both the Cognitive System and Memory System
- It receives feedback from the Cognitive System to update health metrics
- This creates a feedback loop that maintains system health and performance

The flow architecture ensures that information is processed in a structured way, moving from input through processing and memory systems, to cognitive components, and finally to output, with health monitoring throughout.'''
    },
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
