#!/usr/bin/env python3
"""
Enhanced File Matcher with Duplicate Detection and Handling
"""

from difflib import SequenceMatcher
from typing import List, Tuple, Optional, Dict, Any
import re


class EnhancedFileMatcher:
    """
    Smart file matching with duplicate detection and handling
    """
    
    def __init__(self, similarity_threshold=0.6, duplicate_threshold=0.95):
        """
        Args:
            similarity_threshold: Minimum similarity to consider a match (0.6 = 60%)
            duplicate_threshold: Score above which files are considered duplicates (0.95 = 95%)
        """
        self.similarity_threshold = similarity_threshold
        self.duplicate_threshold = duplicate_threshold
    
    def calculate_similarity(self, search_term: str, candidate: str) -> float:
        """Calculate similarity between search term and candidate"""
        search_lower = search_term.lower().strip()
        candidate_lower = candidate.lower().strip()
        
        # Exact match
        if search_lower == candidate_lower:
            return 1.0
        
        # Substring match
        if search_lower in candidate_lower:
            coverage = len(search_lower) / len(candidate_lower)
            return 0.85 + (0.15 * coverage)
        
        # Fuzzy match
        base_similarity = SequenceMatcher(None, search_lower, candidate_lower).ratio()
        
        # Word overlap
        search_words = set(search_lower.split())
        candidate_words = set(candidate_lower.split())
        word_overlap = len(search_words & candidate_words) / max(len(search_words), 1)
        
        # Combined score
        return (base_similarity * 0.7) + (word_overlap * 0.3)
    
    def parse_indexed_search(self, search_term: str) -> Tuple[str, Optional[int]]:
        """
        Parse search term for index notation
        
        Examples:
            "Untitled Document [2]" → ("Untitled Document", 2)
            "Untitled Document #3" → ("Untitled Document", 3)
            "Resume (1)" → ("Resume", 1)
            "Resume" → ("Resume", None)
        
        Returns:
            (clean_search_term, index)
        """
        # Match patterns: [2], #2, (2)
        patterns = [
            r'\s*\[(\d+)\]\s*$',  # [2]
            r'\s*#(\d+)\s*$',      # #2
            r'\s*\((\d+)\)\s*$'    # (2)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, search_term)
            if match:
                index = int(match.group(1))
                clean_term = re.sub(pattern, '', search_term).strip()
                return (clean_term, index)
        
        return (search_term, None)
    
    def find_matches_with_duplicates(self, search_term: str, candidates: List[str], 
                                    max_results: int = 10) -> Dict[str, Any]:
        """
        Find matches and detect duplicates
        
        Returns:
            dict with:
                - 'matches': List of (candidate, score) tuples
                - 'has_duplicates': bool
                - 'duplicate_groups': List of lists of similar matches
                - 'search_term': Original search term
                - 'indexed_search': Parsed search term and index
        """
        # Parse for index notation
        clean_search, requested_index = self.parse_indexed_search(search_term)
        
        # Calculate scores
        scored = [
            (candidate, self.calculate_similarity(clean_search, candidate))
            for candidate in candidates
        ]
        
        # Filter by threshold
        matches = [(c, s) for c, s in scored if s >= self.similarity_threshold]
        
        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Detect duplicates (files with very similar scores)
        duplicate_groups = []
        has_duplicates = False
        
        if len(matches) > 1:
            current_group = [matches[0]]
            
            for i in range(1, len(matches)):
                prev_score = matches[i-1][1]
                curr_score = matches[i][1]
                
                # If scores are very close, they're duplicates
                if abs(prev_score - curr_score) < (1.0 - self.duplicate_threshold):
                    current_group.append(matches[i])
                else:
                    if len(current_group) > 1:
                        duplicate_groups.append(current_group)
                        has_duplicates = True
                    current_group = [matches[i]]
            
            # Don't forget last group
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                has_duplicates = True
        
        return {
            'matches': matches[:max_results],
            'has_duplicates': has_duplicates,
            'duplicate_groups': duplicate_groups,
            'search_term': search_term,
            'clean_search': clean_search,
            'requested_index': requested_index,
            'total_matches': len(matches)
        }
    
    def select_best_match(self, result: Dict[str, Any], 
                         strategy: str = 'first',
                         metadata: Optional[List[Dict]] = None) -> Optional[Tuple[str, float, str]]:
        """
        Select the best match from results
        
        Args:
            result: Result from find_matches_with_duplicates()
            strategy: Selection strategy:
                - 'first': First match (default)
                - 'indexed': Use requested index from search term
                - 'newest': Newest file (requires metadata)
                - 'oldest': Oldest file (requires metadata)
                - 'largest': Largest file (requires metadata)
                - 'ask': Return None to prompt user
            metadata: List of metadata dicts with keys like 'modifiedTime', 'size'
        
        Returns:
            (selected_file, score, reason) or None
        """
        matches = result['matches']
        
        if not matches:
            return None
        
        # Strategy: Use requested index
        if strategy == 'indexed' and result['requested_index'] is not None:
            idx = result['requested_index'] - 1  # Convert to 0-based
            if 0 <= idx < len(matches):
                file, score = matches[idx]
                return (file, score, f"Selected by index #{result['requested_index']}")
            else:
                # Index out of range, fall back to first
                file, score = matches[0]
                return (file, score, f"Index #{result['requested_index']} out of range, using first match")
        
        # Strategy: Ask user
        if strategy == 'ask':
            return None
        
        # Strategy: First match
        if strategy == 'first':
            file, score = matches[0]
            reason = "Highest similarity score"
            if result['has_duplicates']:
                reason += " (duplicates detected - consider using index notation)"
            return (file, score, reason)
        
        # Metadata-based strategies
        if metadata and len(metadata) == len(matches):
            if strategy == 'newest':
                # Sort by modifiedTime (newest first)
                combined = list(zip(matches, metadata))
                combined.sort(key=lambda x: x[1].get('modifiedTime', ''), reverse=True)
                file, score = combined[0][0]
                return (file, score, "Selected by newest modified date")
            
            elif strategy == 'oldest':
                combined = list(zip(matches, metadata))
                combined.sort(key=lambda x: x[1].get('modifiedTime', ''))
                file, score = combined[0][0]
                return (file, score, "Selected by oldest modified date")
            
            elif strategy == 'largest':
                combined = list(zip(matches, metadata))
                combined.sort(key=lambda x: int(x[1].get('size', 0)), reverse=True)
                file, score = combined[0][0]
                return (file, score, "Selected by largest file size")
        
        # Default: first match
        file, score = matches[0]
        return (file, score, "First match (default)")
    
    def format_duplicate_warning(self, result: Dict[str, Any]) -> str:
        """
        Generate a warning message for duplicates
        
        Returns:
            str: Formatted warning message
        """
        if not result['has_duplicates']:
            return ""
        
        warning = f"\n⚠️  DUPLICATE FILES DETECTED!\n"
        warning += f"   Search: '{result['search_term']}'\n"
        warning += f"   Found {result['total_matches']} similar files:\n\n"
        
        for i, (file, score) in enumerate(result['matches'], 1):
            warning += f"   {i}. {file} ({score:.1%})\n"
        
        warning += f"\n   💡 To select a specific file, use index notation:\n"
        warning += f"      '{result['clean_search']} [2]'  or\n"
        warning += f"      '{result['clean_search']} #2'  or\n"
        warning += f"      '{result['clean_search']} (2)'\n"
        
        return warning


# Test the enhanced matcher
if __name__ == '__main__':
    matcher = EnhancedFileMatcher(similarity_threshold=0.6)
    
    # Test files with duplicates
    test_files = [
        "Untitled Document",
        "Untitled Document",
        "Untitled Document",
        "Untitled Document (1)",
        "Untitled Document (2)",
        "Untitled document",
        "Resume.pdf",
        "Ryan Resume.docx",
        "My Resume 2024.pdf"
    ]
    
    print("="*70)
    print("ENHANCED FILE MATCHER - DUPLICATE HANDLING")
    print("="*70)
    
    # Test 1: Basic search with duplicates
    print("\n--- Test 1: Search 'Untitled Document' ---")
    result = matcher.find_matches_with_duplicates("Untitled Document", test_files)
    
    print(f"Found {len(result['matches'])} matches")
    print(f"Has duplicates: {result['has_duplicates']}")
    
    for i, (file, score) in enumerate(result['matches'], 1):
        print(f"  {i}. {file} - {score:.2%}")
    
    if result['has_duplicates']:
        print(matcher.format_duplicate_warning(result))
    
    # Test 2: Indexed search
    print("\n--- Test 2: Search 'Untitled Document [3]' ---")
    result = matcher.find_matches_with_duplicates("Untitled Document [3]", test_files)
    
    print(f"Clean search term: '{result['clean_search']}'")
    print(f"Requested index: {result['requested_index']}")
    
    selection = matcher.select_best_match(result, strategy='indexed')
    if selection:
        file, score, reason = selection
        print(f"\n✓ Selected: '{file}'")
        print(f"  Score: {score:.2%}")
        print(f"  Reason: {reason}")
    
    # Test 3: Different index notations
    print("\n--- Test 3: Different Index Notations ---")
    
    test_searches = [
        "Untitled Document [2]",
        "Untitled Document #1",
        "Untitled Document (4)",
        "Resume [1]"
    ]
    
    for search in test_searches:
        clean, idx = matcher.parse_indexed_search(search)
        print(f"'{search}' → clean: '{clean}', index: {idx}")
    
    # Test 4: Metadata-based selection
    print("\n--- Test 4: Metadata-Based Selection ---")
    
    # Simulate metadata
    metadata = [
        {'modifiedTime': '2024-10-27T10:00:00', 'size': 1024},
        {'modifiedTime': '2024-10-26T10:00:00', 'size': 2048},
        {'modifiedTime': '2024-10-28T10:00:00', 'size': 512},
        {'modifiedTime': '2024-10-25T10:00:00', 'size': 4096},
        {'modifiedTime': '2024-10-24T10:00:00', 'size': 256}
    ]
    
    result = matcher.find_matches_with_duplicates("Untitled Document", test_files)
    
    # Try different strategies
    strategies = ['newest', 'oldest', 'largest']
    for strategy in strategies:
        selection = matcher.select_best_match(result, strategy=strategy, metadata=metadata)
        if selection:
            file, score, reason = selection
            print(f"\n{strategy.upper()}: {file}")
            print(f"  {reason}")
    
    print("\n" + "="*70)