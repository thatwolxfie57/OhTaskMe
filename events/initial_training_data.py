"""
Initial data collection for ML training.

This script provides sample data for the initial training of the task suggestion model.
"""
import json
import os
from django.conf import settings

# Sample event types and their associated tasks
INITIAL_TRAINING_DATA = [
    {
        "event_type": "meeting",
        "samples": [
            {
                "title": "Team weekly meeting",
                "description": "Regular sync meeting with the development team",
                "tasks": [
                    "Prepare agenda for team meeting",
                    "Send meeting invite to all team members",
                    "Book conference room for team meeting",
                    "Prepare presentation slides for the meeting",
                    "Share meeting notes after team meeting"
                ]
            },
            {
                "title": "Client project kickoff",
                "description": "Initial meeting with new client to discuss project requirements",
                "tasks": [
                    "Prepare project proposal for client meeting",
                    "Research client company background",
                    "Create presentation for client meeting",
                    "Send follow-up email after client meeting",
                    "Document client requirements from meeting"
                ]
            }
        ]
    },
    {
        "event_type": "travel",
        "samples": [
            {
                "title": "Business trip to New York",
                "description": "Attending industry conference and client meetings",
                "tasks": [
                    "Book flights for New York trip",
                    "Reserve hotel for New York stay",
                    "Create packing list for business trip",
                    "Notify team about absence during trip",
                    "Prepare presentation for conference talk",
                    "Set up out-of-office email response"
                ]
            },
            {
                "title": "Team retreat",
                "description": "Annual team building retreat at mountain resort",
                "tasks": [
                    "Book accommodation for team retreat",
                    "Plan team building activities",
                    "Arrange transportation to retreat location",
                    "Prepare retreat agenda",
                    "Order team lunch for retreat",
                    "Send retreat details to all participants"
                ]
            }
        ]
    },
    {
        "event_type": "project",
        "samples": [
            {
                "title": "Website redesign launch",
                "description": "Go-live for the new company website redesign",
                "tasks": [
                    "Final QA testing before website launch",
                    "Prepare website content migration",
                    "Set up analytics tracking for new website",
                    "Create backup of current website",
                    "Brief team on launch plan",
                    "Schedule social media announcements for launch",
                    "Monitor website performance after launch"
                ]
            },
            {
                "title": "Product feature release",
                "description": "Release of new product features to customers",
                "tasks": [
                    "Complete feature documentation",
                    "Run final regression tests",
                    "Prepare release notes",
                    "Brief customer support team on new features",
                    "Schedule deployment window",
                    "Send feature announcement to customers",
                    "Monitor system after release"
                ]
            }
        ]
    },
    {
        "event_type": "celebration",
        "samples": [
            {
                "title": "Company holiday party",
                "description": "Annual holiday celebration for all employees",
                "tasks": [
                    "Reserve venue for holiday party",
                    "Select catering menu for party",
                    "Send party invitations to all staff",
                    "Order decorations for holiday party",
                    "Arrange transportation options for staff",
                    "Create party playlist",
                    "Organize gift exchange"
                ]
            },
            {
                "title": "Team member birthday celebration",
                "description": "Office celebration for team member's birthday",
                "tasks": [
                    "Order birthday cake",
                    "Buy birthday card for team member",
                    "Collect money for group gift",
                    "Decorate team member's desk",
                    "Schedule celebration time with team",
                    "Remind team about celebration"
                ]
            }
        ]
    },
    {
        "event_type": "training",
        "samples": [
            {
                "title": "Technical skills workshop",
                "description": "Workshop to improve team's coding skills",
                "tasks": [
                    "Prepare workshop materials and exercises",
                    "Set up development environment for participants",
                    "Book training room for workshop",
                    "Send pre-workshop reading materials",
                    "Create feedback form for workshop",
                    "Follow up with participants after workshop"
                ]
            },
            {
                "title": "Conference attendance",
                "description": "Attending industry conference for professional development",
                "tasks": [
                    "Register for conference",
                    "Book travel and accommodation",
                    "Review conference schedule and select sessions",
                    "Prepare questions for networking opportunities",
                    "Share learnings with team after conference",
                    "Follow up with contacts made at conference"
                ]
            }
        ]
    },
    {
        "event_type": "interview",
        "samples": [
            {
                "title": "Developer job interview",
                "description": "Interview with candidate for software developer position",
                "tasks": [
                    "Review candidate resume before interview",
                    "Prepare technical questions for interview",
                    "Book meeting room for interview",
                    "Notify reception about candidate arrival",
                    "Prepare coding test for candidate",
                    "Submit interview feedback after meeting"
                ]
            },
            {
                "title": "Team lead hiring panel",
                "description": "Final round interviews for team lead position",
                "tasks": [
                    "Review candidate application materials",
                    "Coordinate interview panel schedule",
                    "Prepare leadership scenario questions",
                    "Book interview rooms for the day",
                    "Gather feedback from all interviewers",
                    "Prepare candidate evaluation summary"
                ]
            }
        ]
    }
]

def save_initial_training_data():
    """
    Save the initial training data to a JSON file.
    
    Returns:
        Path to the saved file
    """
    # Create ML models directory if it doesn't exist
    MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_models')
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    # Save the initial training data
    filepath = os.path.join(MODEL_DIR, 'initial_training_data.json')
    
    with open(filepath, 'w') as f:
        json.dump(INITIAL_TRAINING_DATA, f, indent=2)
    
    return filepath
