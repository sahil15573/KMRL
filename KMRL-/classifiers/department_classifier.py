
import re
from typing import Dict, List, Optional
from collections import defaultdict

class DepartmentClassifier:
    """Classify documents by department based on content and keywords"""

    def __init__(self):
        # Department keywords mapping
        self.department_keywords = {
            'ENGINEERING': [
                'engineering', 'technical', 'design', 'construction', 'maintenance',
                'infrastructure', 'track', 'signal', 'electrical', 'mechanical',
                'civil', 'structural', 'rolling stock', 'train', 'locomotive',
                'bridge', 'tunnel', 'station', 'platform', 'overhead', 'catenary',
                'dwg', 'drawing', 'blueprint', 'specification', 'cad'
            ],
            'PROCUREMENT': [
                'procurement', 'purchase', 'vendor', 'supplier', 'contract',
                'quotation', 'tender', 'bid', 'invoice', 'payment', 'order',
                'material', 'equipment', 'spare parts', 'delivery', 'supply',
                'cost', 'price', 'budget', 'negotiation', 'agreement'
            ],
            'HR': [
                'human resource', 'hr', 'employee', 'staff', 'personnel',
                'recruitment', 'hiring', 'training', 'policy', 'leave',
                'attendance', 'payroll', 'benefits', 'performance',
                'disciplinary', 'grievance', 'promotion', 'transfer',
                'resignation', 'termination', 'appraisal'
            ],
            'FINANCE': [
                'finance', 'financial', 'accounting', 'budget', 'expenditure',
                'revenue', 'audit', 'tax', 'billing', 'cost', 'profit',
                'loss', 'balance', 'ledger', 'transaction', 'banking',
                'investment', 'loan', 'insurance', 'claim'
            ],
            'SAFETY': [
                'safety', 'security', 'accident', 'incident', 'hazard',
                'risk', 'emergency', 'fire', 'evacuation', 'first aid',
                'injury', 'fatality', 'ppe', 'personal protective equipment',
                'safety training', 'safety drill', 'safety audit',
                'safety committee', 'safety policy', 'safety manual'
            ],
            'OPERATIONS': [
                'operations', 'operational', 'schedule', 'timetable',
                'service', 'passenger', 'ridership', 'frequency',
                'delay', 'disruption', 'performance', 'punctuality',
                'control room', 'dispatch', 'coordination', 'monitoring'
            ],
            'LEGAL': [
                'legal', 'law', 'regulation', 'compliance', 'court',
                'litigation', 'agreement', 'contract', 'clause',
                'terms', 'conditions', 'liability', 'dispute',
                'arbitration', 'mediation', 'settlement'
            ],
            'REGULATORY': [
                'regulatory', 'regulation', 'compliance', 'commissioner',
                'ministry', 'government', 'authority', 'approval',
                'license', 'permit', 'clearance', 'inspection',
                'audit', 'report', 'submission', 'deadline'
            ]
        }

        # Special patterns for specific departments
        self.department_patterns = {
            'ENGINEERING': [
                r'\b(dwg|dxf)\b',
                r'drawing\s+no',
                r'technical\s+specification',
                r'design\s+document'
            ],
            'PROCUREMENT': [
                r'po\s+no',
                r'purchase\s+order',
                r'vendor\s+code',
                r'invoice\s+no'
            ],
            'FINANCE': [
                r'₹|\$|usd|inr',
                r'\b\d+\.\d+\s*(crore|lakh|million)',
                r'account\s+no',
                r'transaction\s+id'
            ],
            'SAFETY': [
                r'accident\s+report',
                r'incident\s+no',
                r'safety\s+violation'
            ]
        }

    def classify(self, text: str, filename: str = "", meta_data: Dict = None) -> Dict[str, any]:
        """
        Classify document by department
        Returns: {
            'department': str,
            'confidence': float,
            'scores': dict,
            'reasoning': list
        }
        """
        if not text:
            return {
                'department': 'UNKNOWN',
                'confidence': 0.0,
                'scores': {},
                'reasoning': ['No text content to analyze']
            }

        text_lower = text.lower()
        filename_lower = filename.lower()

        # Calculate scores for each department
        dept_scores = defaultdict(float)
        reasoning = []

        # 1. Keyword-based scoring
        for dept, keywords in self.department_keywords.items():
            keyword_score = 0
            matched_keywords = []

            for keyword in keywords:
                keyword_count = text_lower.count(keyword.lower())
                if keyword_count > 0:
                    keyword_score += keyword_count
                    matched_keywords.append(f"{keyword}({keyword_count})")

            if keyword_score > 0:
                dept_scores[dept] += keyword_score * 0.5  # Weight for keywords
                reasoning.append(f"{dept}: Keywords {matched_keywords}")

        # 2. Pattern-based scoring
        for dept, patterns in self.department_patterns.items():
            pattern_score = 0
            matched_patterns = []

            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    pattern_score += len(matches)
                    matched_patterns.append(f"{pattern}({len(matches)})")

            if pattern_score > 0:
                dept_scores[dept] += pattern_score * 0.8  # Higher weight for patterns
                reasoning.append(f"{dept}: Patterns {matched_patterns}")

        # 3. Filename-based hints
        filename_hints = {
            'ENGINEERING': ['dwg', 'dxf', 'design', 'tech', 'drawing'],
            'PROCUREMENT': ['po', 'purchase', 'vendor', 'invoice'],
            'HR': ['hr', 'employee', 'staff', 'personnel'],
            'FINANCE': ['finance', 'budget', 'cost', 'payment'],
            'SAFETY': ['safety', 'accident', 'incident'],
            'OPERATIONS': ['ops', 'operation', 'schedule', 'service']
        }

        for dept, hints in filename_hints.items():
            for hint in hints:
                if hint in filename_lower:
                    dept_scores[dept] += 0.3
                    reasoning.append(f"{dept}: Filename hint '{hint}'")

        # 4. File type based hints
        if meta_data:
            file_type = meta_data.get('file_type', '')
            if file_type in ['DWG', 'DXF']:
                dept_scores['ENGINEERING'] += 1.0
                reasoning.append(f"ENGINEERING: CAD file type {file_type}")
            elif file_type == 'IMAGE' and any(word in filename_lower for word in ['scan', 'photo', 'img']):
                # Could be any department, but often operational
                dept_scores['OPERATIONS'] += 0.2

        # Determine final classification
        if not dept_scores:
            return {
                'department': 'GENERAL',
                'confidence': 0.0,
                'scores': {},
                'reasoning': ['No department-specific indicators found']
            }

        # Find department with highest score
        top_dept = max(dept_scores.items(), key=lambda x: x[1])
        department = top_dept[0]
        max_score = top_dept[1]

        # Calculate confidence (normalize by text length and maximum possible score)
        text_length_factor = min(len(text) / 1000, 1.0)  # Normalize by 1000 chars
        confidence = min(max_score * text_length_factor / 10, 1.0)  # Cap at 1.0

        return {
            'department': department,
            'confidence': confidence,
            'scores': dict(dept_scores),
            'reasoning': reasoning
        }

    def get_department_list(self) -> List[str]:
        """Get list of all supported departments"""
        return list(self.department_keywords.keys()) + ['GENERAL', 'UNKNOWN']

    def add_keywords(self, department: str, keywords: List[str]):
        """Add custom keywords for a department"""
        if department not in self.department_keywords:
            self.department_keywords[department] = []
        self.department_keywords[department].extend(keywords)

    def add_pattern(self, department: str, pattern: str):
        """Add custom regex pattern for a department"""
        if department not in self.department_patterns:
            self.department_patterns[department] = []
        self.department_patterns[department].append(pattern)
