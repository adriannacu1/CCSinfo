"""
Test script to verify event management functionality
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://127.0.0.1:5000'

def test_event_management():
    """Test the event management system"""
    
    # Test data for creating events
    sample_events = [
        {
            'title': 'Python Programming Workshop',
            'description': 'Learn Python programming from basics to advanced concepts. Perfect for beginners and intermediate programmers.',
            'category': 'workshop',
            'event_date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'event_time': '09:00',
            'end_time': '17:00',
            'location': 'CCS Computer Lab 1',
            'price': 50.00,
            'status': 'upcoming',
            'featured_image': 'https://images.unsplash.com/photo-1526379879527-8559ecfcaec0?w=800&h=400&fit=crop',
            'speakers': [
                {
                    'name': 'Dr. Sarah Johnson',
                    'role': 'Senior Python Developer',
                    'bio': 'Expert Python developer with 10+ years of experience in web development and data science.'
                },
                {
                    'name': 'Mark Thompson',
                    'role': 'DevOps Engineer',
                    'bio': 'Experienced in Python automation and deployment strategies.'
                }
            ]
        },
        {
            'title': 'AI & Machine Learning Conference 2025',
            'description': 'Join leading experts in AI and ML for a day of cutting-edge presentations and networking.',
            'category': 'conference',
            'event_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'event_time': '08:00',
            'end_time': '18:00',
            'location': 'CCS Main Auditorium',
            'price': 0.00,
            'status': 'upcoming',
            'featured_image': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&h=400&fit=crop',
            'speakers': [
                {
                    'name': 'Prof. Emily Chen',
                    'role': 'AI Research Director',
                    'bio': 'Leading researcher in artificial intelligence and neural networks.'
                },
                {
                    'name': 'Dr. Michael Rodriguez',
                    'role': 'ML Engineering Manager',
                    'bio': 'Experienced in deploying machine learning models at scale.'
                },
                {
                    'name': 'Lisa Wang',
                    'role': 'Data Scientist',
                    'bio': 'Expert in predictive analytics and deep learning applications.'
                }
            ]
        },
        {
            'title': 'Cybersecurity Bootcamp',
            'description': 'Intensive hands-on training covering ethical hacking, penetration testing, and security best practices.',
            'category': 'workshop',
            'event_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'event_time': '13:00',
            'end_time': '17:00',
            'location': 'CCS Security Lab',
            'price': 75.00,
            'status': 'upcoming',
            'featured_image': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&h=400&fit=crop',
            'speakers': [
                {
                    'name': 'Alex Mitchell',
                    'role': 'Cybersecurity Consultant',
                    'bio': 'Certified ethical hacker with expertise in penetration testing and vulnerability assessment.'
                }
            ]
        }
    ]
    
    print("Event Management Test Script")
    print("=" * 40)
    
    # Note: This script assumes you have admin authentication set up
    # In a real scenario, you would need to login first to get session cookies
    print("Note: Make sure you're logged in as admin in your browser to test the API endpoints.")
    print("\nSample events that can be created:")
    
    for i, event in enumerate(sample_events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Category: {event['category']}")
        print(f"   Date: {event['event_date']} {event['event_time']}")
        print(f"   Location: {event['location']}")
        print(f"   Price: ${event['price']}")
        print(f"   Speakers: {len(event['speakers'])}")
    
    print("\n" + "=" * 40)
    print("Event management system is ready!")
    print("Visit http://127.0.0.1:5000/admin/events to test the interface.")

if __name__ == '__main__':
    test_event_management()
