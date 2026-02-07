"""
Task suggestion module using NLP and ML techniques to generate tasks based on event information.
"""
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import datetime
from django.utils import timezone

# Load NLP models
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

"""
Enhanced AI Task suggestion module using advanced NLP and context analysis.

Phase 1: Enhanced Context Analysis - IMPLEMENTED
Phase 2: User-Centric Intelligence - TODO: Implement user profiles and preferences
Phase 3: Machine Learning Integration - TODO: Implement predictive models and learning

TODO: Add user profile integration for personalized suggestions
TODO: Implement machine learning models for task success prediction
TODO: Add user behavior tracking and adaptive learning
TODO: Create advanced analytics and insights system
"""
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import datetime
from django.utils import timezone
from collections import defaultdict
import math

# Load NLP models
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

# Enhanced event classification with intelligent context analysis
class EventAnalyzer:
    """
    Enhanced event analyzer with intelligent context understanding.
    
    TODO: Integrate with user profiles for personalized analysis
    TODO: Add machine learning models for better classification accuracy
    TODO: Implement user feedback integration for continuous improvement
    """
    
    # Comprehensive event patterns with context and complexity indicators
    EVENT_CATEGORIES = {
        'meeting': {
            'patterns': [
                r'\b(meeting|conference|call|discussion|sync|standup|review|presentation)\b',
                r'\b(client|team|board|staff|committee)\b.*\b(meeting|call)\b',
                r'\b(zoom|teams|skype|webex)\b.*\b(call|meeting)\b'
            ],
            'complexity_factors': {
                'high': ['board', 'client', 'presentation', 'conference', 'annual'],
                'medium': ['team', 'review', 'planning', 'quarterly'],
                'low': ['standup', 'sync', 'quick', 'brief', 'check-in']
            },
            'base_prep_days': 2,
            'tasks': [
                {'template': 'Review agenda and prepare talking points for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Gather relevant documents and materials for {event_title}', 'complexity_multiplier': 0.8},
                {'template': 'Test technology setup for {event_title}', 'complexity_multiplier': 0.3},
                {'template': 'Send reminder and confirmation for {event_title}', 'complexity_multiplier': 0.2},
                {'template': 'Follow up with action items from {event_title}', 'days_after': 1, 'complexity_multiplier': 0.5}
            ]
        },
        
        'exam_study': {
            'patterns': [
                r'\b(exam|test|quiz|assessment|evaluation|midterm|final)\b',
                r'\b(study|preparation|review)\b.*\b(exam|test)\b',
                r'\b(examination|assessment)\b',
                r'\bmid\s*(semester|term)\s*(exam|test|assessment)\b',
                r'\b(semester|term)\s*(exam|test|assessment)\b'
            ],
            'complexity_factors': {
                'high': ['final', 'comprehensive', 'board', 'certification', 'licensing'],
                'medium': ['midterm', 'unit', 'module', 'chapter'],
                'low': ['quiz', 'pop', 'quick', 'review']
            },
            'base_prep_days': 7,
            'tasks': [
                {'template': 'Create study schedule for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Review course materials and notes for {event_title}', 'complexity_multiplier': 1.2},
                {'template': 'Practice problems and past papers for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Create summary notes and flashcards for {event_title}', 'complexity_multiplier': 0.8},
                {'template': 'Final review session for {event_title}', 'days_before': 1, 'complexity_multiplier': 0.6},
                {'template': 'Gather exam materials and check requirements for {event_title}', 'days_before': 1, 'complexity_multiplier': 0.3}
            ]
        },
        
        'travel': {
            'patterns': [
                r'\b(trip|travel|flight|journey|vacation|holiday|tour)\b',
                r'\b(business|work)\s+(trip|travel)\b',
                r'\b(conference|seminar)\b.*\b(travel|trip)\b'
            ],
            'complexity_factors': {
                'high': ['international', 'business', 'conference', 'extended', 'family'],
                'medium': ['domestic', 'weekend', 'short', 'personal'],
                'low': ['day', 'local', 'nearby']
            },
            'base_prep_days': 5,
            'tasks': [
                {'template': 'Research and book transportation for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Arrange accommodation for {event_title}', 'complexity_multiplier': 0.9},
                {'template': 'Create packing checklist for {event_title}', 'complexity_multiplier': 0.6},
                {'template': 'Check weather and prepare appropriate clothing for {event_title}', 'complexity_multiplier': 0.4},
                {'template': 'Arrange transportation to airport/station for {event_title}', 'complexity_multiplier': 0.5},
                {'template': 'Check travel documents and requirements for {event_title}', 'complexity_multiplier': 0.7},
                {'template': 'Pack essentials and final preparations for {event_title}', 'days_before': 1, 'complexity_multiplier': 0.3}
            ]
        },
        
        'project': {
            'patterns': [
                r'\b(project|deadline|launch|release|deployment|milestone)\b',
                r'\b(deliverable|submission|presentation)\b.*\b(due|deadline)\b',
                r'\b(sprint|iteration)\b.*\b(review|demo)\b'
            ],
            'complexity_factors': {
                'high': ['major', 'critical', 'launch', 'release', 'final'],
                'medium': ['milestone', 'phase', 'module', 'component'],
                'low': ['minor', 'update', 'patch', 'quick']
            },
            'base_prep_days': 10,
            'tasks': [
                {'template': 'Break down project scope and create timeline for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Assign resources and responsibilities for {event_title}', 'complexity_multiplier': 0.8},
                {'template': 'Set up project tracking and communication channels for {event_title}', 'complexity_multiplier': 0.6},
                {'template': 'Create quality assurance and testing plan for {event_title}', 'complexity_multiplier': 0.9},
                {'template': 'Prepare documentation and user guides for {event_title}', 'complexity_multiplier': 0.7},
                {'template': 'Final review and testing before {event_title}', 'days_before': 2, 'complexity_multiplier': 0.8},
                {'template': 'Post-project review and documentation for {event_title}', 'days_after': 3, 'complexity_multiplier': 0.6}
            ]
        },
        
        'presentation': {
            'patterns': [
                r'\b(presentation|pitch|demo|speech|talk|lecture)\b',
                r'\b(present|presenting)\b.*\b(to|at|for)\b',
                r'\b(keynote|workshop|seminar)\b'
            ],
            'complexity_factors': {
                'high': ['keynote', 'conference', 'board', 'client', 'public'],
                'medium': ['team', 'departmental', 'training', 'workshop'],
                'low': ['informal', 'quick', 'update', 'brief']
            },
            'base_prep_days': 5,
            'tasks': [
                {'template': 'Research audience and tailor content for {event_title}', 'complexity_multiplier': 1.0},
                {'template': 'Create presentation outline and structure for {event_title}', 'complexity_multiplier': 0.9},
                {'template': 'Develop slides and visual materials for {event_title}', 'complexity_multiplier': 1.1},
                {'template': 'Practice presentation delivery for {event_title}', 'complexity_multiplier': 0.8},
                {'template': 'Prepare for Q&A and potential questions for {event_title}', 'complexity_multiplier': 0.7},
                {'template': 'Test technical setup and backup plans for {event_title}', 'days_before': 1, 'complexity_multiplier': 0.4},
                {'template': 'Gather feedback and follow up after {event_title}', 'days_after': 1, 'complexity_multiplier': 0.3}
            ]
        },
        
        'appointment': {
            'patterns': [
                r'\b(appointment|consultation|checkup|visit|interview)\b',
                r'\b(doctor|dentist|medical|health)\b.*\b(appointment|visit)\b',
                r'\b(job|employment)\b.*\b(interview|meeting)\b'
            ],
            'complexity_factors': {
                'high': ['job', 'medical', 'specialist', 'important', 'final'],
                'medium': ['consultation', 'interview', 'checkup'],
                'low': ['routine', 'follow-up', 'quick', 'brief']
            },
            'base_prep_days': 2,
            'tasks': [
                {'template': 'Confirm appointment details and location for {event_title}', 'complexity_multiplier': 0.3},
                {'template': 'Prepare necessary documents and information for {event_title}', 'complexity_multiplier': 0.7},
                {'template': 'Research and prepare questions for {event_title}', 'complexity_multiplier': 0.6},
                {'template': 'Plan transportation and allow extra time for {event_title}', 'complexity_multiplier': 0.4},
                {'template': 'Follow up on outcomes and next steps from {event_title}', 'days_after': 1, 'complexity_multiplier': 0.4}
            ]
        },
        
        'social_event': {
            'patterns': [
                r'\b(party|celebration|birthday|anniversary|wedding|gathering)\b',
                r'\b(dinner|lunch|social|hangout|meetup)\b',
                r'\b(holiday|festival|cultural)\b.*\b(event|celebration)\b'
            ],
            'complexity_factors': {
                'high': ['wedding', 'anniversary', 'major', 'formal', 'hosted'],
                'medium': ['birthday', 'celebration', 'dinner', 'gathering'],
                'low': ['casual', 'informal', 'small', 'simple']
            },
            'base_prep_days': 3,
            'tasks': [
                {'template': 'Plan guest list and send invitations for {event_title}', 'complexity_multiplier': 0.8},
                {'template': 'Arrange venue and necessary reservations for {event_title}', 'complexity_multiplier': 0.9},
                {'template': 'Plan menu, catering, or restaurant for {event_title}', 'complexity_multiplier': 0.7},
                {'template': 'Choose appropriate outfit or attire for {event_title}', 'complexity_multiplier': 0.3},
                {'template': 'Prepare gifts, cards, or contributions for {event_title}', 'complexity_multiplier': 0.5},
                {'template': 'Send thank you messages after {event_title}', 'days_after': 1, 'complexity_multiplier': 0.2}
            ]
        }
    }

    def analyze_event_complexity(self, title, description="", location="", duration_hours=1):
        """
        Analyze event complexity using multiple factors.
        
        TODO: Integrate with user profile to personalize complexity assessment
        TODO: Add machine learning model for more accurate complexity prediction
        TODO: Consider user's historical performance with similar events
        
        Args:
            title: Event title
            description: Event description
            location: Event location
            duration_hours: Event duration
            
        Returns:
            dict: Complexity analysis with score and factors
        """
        text = f"{title} {description} {location}".lower()
        
        # Base complexity factors
        complexity_score = 1.0
        factors = []
        
        # Duration factor
        if duration_hours > 4:
            complexity_score *= 1.5
            factors.append("long duration")
        elif duration_hours > 8:
            complexity_score *= 2.0
            factors.append("very long duration")
        
        # Location complexity
        if any(word in location.lower() for word in ['international', 'airport', 'conference center']):
            complexity_score *= 1.3
            factors.append("complex location")
        
        # Keywords indicating complexity
        high_complexity_words = ['critical', 'important', 'major', 'final', 'board', 'client', 'public']
        for word in high_complexity_words:
            if word in text:
                complexity_score *= 1.2
                factors.append(f"high-priority keyword: {word}")
        
        # Multiple stakeholders
        stakeholder_words = ['team', 'client', 'board', 'committee', 'group', 'department']
        stakeholder_count = sum(1 for word in stakeholder_words if word in text)
        if stakeholder_count > 0:
            complexity_score *= (1 + 0.1 * stakeholder_count)
            factors.append(f"multiple stakeholders ({stakeholder_count})")
        
        return {
            'score': min(complexity_score, 3.0),  # Cap at 3x complexity
            'factors': factors,
            'category': self._get_complexity_category(complexity_score)
        }

    def _get_complexity_category(self, score):
        """Categorize complexity score into low/medium/high."""
        if score >= 2.0:
            return 'high'
        elif score >= 1.3:
            return 'medium'
        else:
            return 'low'

    def classify_event_type(self, title, description="", location=""):
        """
        Enhanced event classification using NLP and context analysis.
        
        TODO: Add machine learning classification model
        TODO: Implement user-specific event type learning
        TODO: Add confidence scoring for classifications
        
        Args:
            title: Event title
            description: Event description
            location: Event location
            
        Returns:
            dict: Classification results with type, confidence, and context
        """
        text = f"{title} {description} {location}"
        
        # NLP processing
        doc = nlp(text.lower())
        
        # Extract entities and their types
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Score each category
        category_scores = {}
        for category, config in self.EVENT_CATEGORIES.items():
            score = 0
            matched_patterns = []
            
            # Pattern matching with weighted scoring
            for i, pattern in enumerate(config['patterns']):
                matches = re.findall(pattern, text.lower())
                if matches:
                    # Give higher weight to more specific patterns (later in the list)
                    pattern_weight = (i + 1) * 10
                    score += len(matches) * pattern_weight
                    matched_patterns.extend(matches)
            
            # Strong bonus for exact category keywords in title (not just description)
            title_lower = title.lower()
            category_keywords = {
                'exam_study': ['exam', 'test', 'quiz', 'midterm', 'final', 'assessment'],
                'meeting': ['meeting', 'conference', 'call', 'discussion'],
                'travel': ['trip', 'travel', 'flight', 'vacation'],
                'project': ['project', 'deadline', 'launch', 'release'],
                'presentation': ['presentation', 'pitch', 'demo', 'speech'],
                'appointment': ['appointment', 'consultation', 'checkup'],
                'social_event': ['party', 'celebration', 'birthday', 'wedding']
            }
            
            if category in category_keywords:
                for keyword in category_keywords[category]:
                    if keyword in title_lower:
                        score += 50  # Strong bonus for title keywords
            
            # Complexity factor bonus
            for complexity_level, keywords in config['complexity_factors'].items():
                for keyword in keywords:
                    if keyword in text.lower():
                        if complexity_level == 'high':
                            score += 5
                        elif complexity_level == 'medium':
                            score += 3
                        else:
                            score += 1
            
            category_scores[category] = {
                'score': score,
                'matched_patterns': matched_patterns,
                'entities': [ent for ent in entities if ent[0] in text.lower()]
            }
        
        # Find best match
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
        best_score = category_scores[best_category]['score']
        
        # Calculate confidence
        total_score = sum(cat['score'] for cat in category_scores.values())
        confidence = (best_score / max(total_score, 1)) * 100 if total_score > 0 else 50
        
        # Fallback to generic if confidence is too low
        if confidence < 30:
            best_category = 'general'
            confidence = 50
        
        return {
            'type': best_category,
            'confidence': min(confidence, 95),  # Cap confidence at 95%
            'matched_patterns': category_scores.get(best_category, {}).get('matched_patterns', []),
            'entities': category_scores.get(best_category, {}).get('entities', []),
            'all_scores': {k: v['score'] for k, v in category_scores.items()}
        }

# Initialize the analyzer
event_analyzer = EventAnalyzer()

# Enhanced utility functions
def extract_keywords(text):
    """
    Enhanced keyword extraction using NLP techniques.
    
    TODO: Implement TF-IDF scoring for keyword importance
    TODO: Add domain-specific keyword dictionaries
    TODO: Integrate with user's personal keyword preferences
    
    Args:
        text: The text to analyze
        
    Returns:
        A list of important keywords with confidence scores
    """
    # Process the text with spaCy
    doc = nlp(text.lower())
    
    # Extract various types of meaningful tokens
    keywords = []
    
    for token in doc:
        # Skip stop words, punctuation, and spaces
        if token.text in stop_words or token.is_punct or token.is_space:
            continue
            
        # Include important parts of speech
        if token.pos_ in ["NOUN", "VERB", "PROPN", "ADJ"]:
            keywords.append({
                'word': token.lemma_,
                'pos': token.pos_,
                'importance': _calculate_keyword_importance(token)
            })
    
    # Extract named entities
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "PRODUCT"]:
            keywords.append({
                'word': ent.text.lower(),
                'pos': 'ENTITY',
                'entity_type': ent.label_,
                'importance': 0.9  # Entities are usually important
            })
    
    # Sort by importance and remove duplicates
    unique_keywords = {}
    for kw in keywords:
        word = kw['word']
        if word not in unique_keywords or kw['importance'] > unique_keywords[word]['importance']:
            unique_keywords[word] = kw
    
    return sorted(unique_keywords.values(), key=lambda x: x['importance'], reverse=True)

def _calculate_keyword_importance(token):
    """
    Calculate importance score for a keyword token.
    
    TODO: Implement machine learning model for importance scoring
    TODO: Add context-aware importance calculation
    """
    importance = 0.5  # Base importance
    
    # Proper nouns are more important
    if token.pos_ == "PROPN":
        importance += 0.3
    
    # Verbs in certain forms are important
    if token.pos_ == "VERB" and token.tag_ in ["VB", "VBG", "VBN"]:
        importance += 0.2
    
    # Longer words tend to be more specific/important
    if len(token.text) > 6:
        importance += 0.1
    
    return min(importance, 1.0)

def classify_event_type(title, description=""):
    """
    Enhanced event classification using the new EventAnalyzer.
    
    TODO: Maintain backward compatibility while upgrading callers
    TODO: Add deprecation warning for direct usage
    
    Args:
        title: The event title
        description: The event description (optional)
        
    Returns:
        The event type classification
    """
    # Use the new enhanced analyzer
    classification = event_analyzer.classify_event_type(title, description)
    
    # Return just the type for backward compatibility
    # TODO: Update all callers to use the full classification result
    return classification['type']

def generate_task_suggestions(event):
    """
    Enhanced task generation using intelligent context analysis.
    
    TODO: Integrate with user profile preferences for personalization
    TODO: Add machine learning model for task success prediction
    TODO: Implement user feedback loop for continuous improvement
    TODO: Add workload balancing across user's schedule
    
    Args:
        event: The Event object
        
    Returns:
        A list of suggested tasks with descriptions, scheduled times, and confidence scores
    """
    title = event.title
    description = event.description if hasattr(event, 'description') else ""
    location = event.location if hasattr(event, 'location') else ""
    start_time = event.start_time
    end_time = event.end_time
    
    # Calculate event duration
    duration = end_time - start_time
    duration_hours = duration.total_seconds() / 3600
    
    # Analyze event using enhanced classification
    classification = event_analyzer.classify_event_type(title, description, location)
    complexity = event_analyzer.analyze_event_complexity(title, description, location, duration_hours)
    
    # Get event category configuration
    event_type = classification['type']
    if event_type not in event_analyzer.EVENT_CATEGORIES:
        event_type = 'appointment'  # Default fallback
    
    category_config = event_analyzer.EVENT_CATEGORIES[event_type]
    
    # Calculate dynamic preparation time based on complexity
    base_prep_days = category_config['base_prep_days']
    complexity_multiplier = complexity['score']
    total_prep_days = int(base_prep_days * complexity_multiplier)
    
    # Generate tasks based on category and complexity
    suggested_tasks = []
    task_templates = category_config['tasks']
    
    for task_template in task_templates:
        # Calculate task-specific timing
        days_before = task_template.get('days_before', None)
        days_after = task_template.get('days_after', None)
        template_complexity = task_template.get('complexity_multiplier', 1.0)
        
        # Skip tasks that don't meet complexity threshold
        if template_complexity * complexity['score'] < 0.5:
            continue
        
        # Calculate scheduled time
        if days_after:
            scheduled_time = end_time + timezone.timedelta(days=days_after)
            relation = 'after'
        else:
            if days_before:
                scheduled_time = start_time - timezone.timedelta(days=days_before)
            else:
                # Distribute across preparation period
                prep_offset = total_prep_days * template_complexity
                scheduled_time = start_time - timezone.timedelta(days=prep_offset)
            relation = 'before'
        
        # Generate task description
        task_description = task_template['template'].format(event_title=title)
        
        # Calculate confidence based on classification confidence and template match
        base_confidence = classification['confidence']  # This is 0-95
        
        # Convert to 0-1 scale for calculation
        base_confidence_normalized = base_confidence / 100.0
        
        # Apply template complexity multiplier (0.3 to 1.2 range)
        task_confidence_normalized = base_confidence_normalized * template_complexity
        
        # Convert back to percentage and cap at 95%
        task_confidence = min(task_confidence_normalized * 100, 95)
        
        # Adjust confidence based on complexity match
        if complexity['category'] == 'high' and template_complexity > 0.8:
            task_confidence = min(task_confidence * 1.05, 95)  # Small boost
        elif complexity['category'] == 'low' and template_complexity < 0.5:
            task_confidence = min(task_confidence * 1.05, 95)  # Small boost
        
        suggested_tasks.append({
            'description': task_description,
            'scheduled_time': scheduled_time,
            'relation': relation,
            'confidence': int(task_confidence),
            'category': event_type,
            'complexity_factor': template_complexity,
            'analysis_notes': f"Based on {event_type} pattern with {complexity['category']} complexity"
        })
    
    # Sort tasks by scheduled time
    suggested_tasks.sort(key=lambda x: x['scheduled_time'])
    
    # Add metadata about the analysis
    analysis_metadata = {
        'event_classification': classification,
        'complexity_analysis': complexity,
        'total_tasks_generated': len(suggested_tasks),
        'preparation_days': total_prep_days,
        'suggestions_quality': 'high' if classification['confidence'] > 70 else 'medium'
    }
    
    # TODO: Log analysis for machine learning training data
    # TODO: Check against user's existing schedule for conflicts
    # TODO: Apply user preference filters
    
    return suggested_tasks

# Enhanced utility functions for backward compatibility and future features

def get_feedback_for_suggestions(accepted_tasks, rejected_tasks, event):
    """
    Process user feedback on task suggestions to improve future suggestions.
    
    Args:
        accepted_tasks: List of task suggestions that were accepted
        rejected_tasks: List of task suggestions that were rejected
        event: The Event object
        
    Returns:
        None (in a real system, this would update a model)
    """
    # In a real system, this would update weights or train a model
    # For now, we'll just log the feedback
    print(f"Feedback for event '{event.title}':")
    print(f"Accepted tasks: {len(accepted_tasks)}")
    print(f"Rejected tasks: {len(rejected_tasks)}")
    
    # This would be where you'd update a model or weights
    # In a production system, you might store this data for later training


# Event patterns dictionary for classification and task generation
EVENT_PATTERNS = {
    'meeting': {
        'keywords': ['meeting', 'discussion', 'sync', 'standup', 'conference', 'call'],
        'tasks': ['prepare agenda', 'book room', 'send invites', 'prepare materials']
    },
    'presentation': {
        'keywords': ['presentation', 'demo', 'pitch', 'showcase', 'review'],
        'tasks': ['create slides', 'practice presentation', 'prepare handouts', 'test equipment']
    },
    'travel': {
        'keywords': ['trip', 'travel', 'flight', 'hotel', 'visit', 'conference'],
        'tasks': ['book flights', 'reserve hotel', 'prepare itinerary', 'pack luggage']
    },
    'project': {
        'keywords': ['project', 'deadline', 'submission', 'deliverable', 'milestone'],
        'tasks': ['review requirements', 'check progress', 'prepare deliverables', 'coordinate team']
    },
    'workshop': {
        'keywords': ['workshop', 'training', 'seminar', 'tutorial', 'learning'],
        'tasks': ['prepare materials', 'book venue', 'organize supplies', 'create agenda']
    }
}


def calculate_confidence(event, task_description):
    """
    Calculate confidence score for a task suggestion based on event context.
    
    Args:
        event: Event object
        task_description: String description of the suggested task
        
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    confidence = 0.5  # Base confidence
    
    # Analyze event type relevance
    event_type = classify_event_type(event.title, event.description)
    if event_type in EVENT_PATTERNS:
        pattern_keywords = EVENT_PATTERNS[event_type]['keywords']
        pattern_tasks = EVENT_PATTERNS[event_type]['tasks']
        
        # Check if task description matches pattern tasks
        task_lower = task_description.lower()
        for pattern_task in pattern_tasks:
            if pattern_task in task_lower:
                confidence += 0.3
                break
    
    # Analyze keyword relevance
    event_keywords = extract_keywords(event.title + ' ' + event.description)
    task_keywords = extract_keywords(task_description)
    
    # Calculate keyword overlap
    common_keywords = set(event_keywords) & set(task_keywords)
    if event_keywords:
        keyword_overlap = len(common_keywords) / len(event_keywords)
        confidence += keyword_overlap * 0.2
    
    # Ensure confidence is within bounds
    return min(max(confidence, 0.0), 1.0)


def classify_event_type(title, description):
    """
    Classify event type based on title and description.
    
    Args:
        title: Event title
        description: Event description
        
    Returns:
        str: Event type classification
    """
    text = (title + ' ' + description).lower()
    
    # Score each event type based on keyword matches
    type_scores = {}
    for event_type, pattern in EVENT_PATTERNS.items():
        score = 0
        for keyword in pattern['keywords']:
            if keyword in text:
                score += 1
        type_scores[event_type] = score
    
    # Return the type with highest score, or 'general' if no matches
    if type_scores and max(type_scores.values()) > 0:
        return max(type_scores.items(), key=lambda x: x[1])[0]
    return 'general'


def extract_keywords(text):
    """
    Extract relevant keywords from text using NLP.
    
    Args:
        text: Input text to analyze
        
    Returns:
        list: List of extracted keywords
    """
    if not text:
        return []
    
    # Process with spaCy
    doc = nlp(text.lower())
    
    keywords = []
    for token in doc:
        # Include nouns, verbs, and adjectives that are not stop words
        if (token.pos_ in ['NOUN', 'VERB', 'ADJ'] and 
            not token.is_stop and 
            not token.is_punct and 
            len(token.text) > 2):
            keywords.append(token.lemma_)
    
    return list(set(keywords))  # Remove duplicates
