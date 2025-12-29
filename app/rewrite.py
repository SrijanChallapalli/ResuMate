"""
Deterministic resume bullet rewriting engine.
Uses templates and verb replacement - NO LLMs.
"""
import re
from typing import List


class ResumeRewriter:
    """Rewrites resume bullets in FAANG-style format."""
    
    # Strong action verbs for different categories
    ACTION_VERBS = {
        'weak': ['did', 'made', 'worked', 'helped', 'used', 'was', 'were'],
        'strong': {
            'achievement': ['achieved', 'delivered', 'executed', 'implemented', 'launched', 'optimized', 'scaled'],
            'leadership': ['led', 'managed', 'coordinated', 'orchestrated', 'spearheaded', 'drove'],
            'technical': ['architected', 'developed', 'designed', 'built', 'engineered', 'automated'],
            'impact': ['improved', 'increased', 'reduced', 'enhanced', 'accelerated', 'streamlined']
        }
    }
    
    # Quantification patterns
    QUANTIFIERS = [
        'by {amount}%', 'by ${amount}', 'to {amount} users', 'by {amount}x',
        'from {before} to {after}', 'over {period}', 'across {number} teams'
    ]
    
    def extract_bullets(self, resume_text: str, max_bullets: int = 10) -> List[str]:
        """
        Extract bullet points from resume text.
        Looks for lines starting with bullets, dashes, or numbered items.
        """
        bullets = []
        lines = resume_text.split('\n')
        
        bullet_pattern = re.compile(r'^[\s]*[•\-\*\+]\s*(.+)$')
        numbered_pattern = re.compile(r'^[\s]*\d+[\.\)]\s*(.+)$')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for bullet format
            match = bullet_pattern.match(line) or numbered_pattern.match(line)
            if match:
                bullet_text = match.group(1).strip()
                if len(bullet_text) > 20:  # Only meaningful bullets
                    bullets.append(bullet_text)
            
            # Also check for lines that look like bullets (short, action-oriented)
            elif len(line) > 20 and len(line) < 200:
                # Check if it starts with a verb (likely a bullet)
                first_word = line.split()[0].lower() if line.split() else ''
                if first_word.endswith('ed') or first_word.endswith('ing'):
                    bullets.append(line)
        
        return bullets[:max_bullets]
    
    def strengthen_verb(self, text: str) -> str:
        """Replace weak verbs with strong action verbs."""
        words = text.split()
        if not words:
            return text
        
        first_word_lower = words[0].lower()
        
        # Check if first word is a weak verb
        if first_word_lower in self.ACTION_VERBS['weak']:
            # Determine category based on context
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['team', 'group', 'led', 'manage']):
                replacement = 'Led'
            elif any(word in text_lower for word in ['code', 'system', 'software', 'application', 'api']):
                replacement = 'Developed'
            elif any(word in text_lower for word in ['improve', 'increase', 'reduce', 'optimize']):
                replacement = 'Improved'
            else:
                replacement = 'Delivered'
            
            words[0] = replacement
            return ' '.join(words)
        
        # Capitalize first word if needed
        if words[0][0].islower():
            words[0] = words[0].capitalize()
        
        return ' '.join(words)
    
    def add_quantification(self, text: str) -> str:
        """
        Add quantification placeholder if missing.
        Looks for numbers, percentages, or dollar amounts.
        """
        # Check if already has quantification
        has_number = bool(re.search(r'\d+', text))
        has_percent = '%' in text
        has_dollar = '$' in text
        
        if has_number or has_percent or has_dollar:
            return text  # Already quantified
        
        # Add a generic quantification placeholder
        # Insert before the last sentence or at the end
        if text.endswith('.'):
            text = text[:-1]
        
        # Try to add quantification naturally
        if 'improved' in text.lower() or 'increased' in text.lower():
            text += ', resulting in improved performance'
        elif 'reduced' in text.lower() or 'decreased' in text.lower():
            text += ', reducing costs and time'
        elif 'developed' in text.lower() or 'built' in text.lower():
            text += ', enabling scalable solutions'
        else:
            text += ', delivering measurable impact'
        
        if not text.endswith('.'):
            text += '.'
        
        return text
    
    def rewrite_bullet(self, bullet: str) -> str:
        """
        Rewrite a single bullet point in FAANG style.
        - Strengthen verbs
        - Add quantification if missing
        - Ensure proper formatting
        """
        if not bullet or len(bullet.strip()) < 10:
            return bullet
        
        # Clean up the bullet
        bullet = bullet.strip()
        
        # Remove leading/trailing punctuation issues
        bullet = re.sub(r'^[^\w]+', '', bullet)
        
        # Strengthen verb
        bullet = self.strengthen_verb(bullet)
        
        # Add quantification if missing
        bullet = self.add_quantification(bullet)
        
        # Ensure proper capitalization and punctuation
        if not bullet[0].isupper():
            bullet = bullet[0].upper() + bullet[1:]
        
        if not bullet.endswith(('.', '!', '?')):
            bullet += '.'
        
        return bullet
    
    def rewrite_bullets(self, resume_text: str, count: int = 3) -> List[str]:
        """
        Extract and rewrite resume bullets.
        Returns up to 'count' rewritten bullets.
        """
        bullets = self.extract_bullets(resume_text, max_bullets=count * 2)
        
        if not bullets:
            # Fallback: create example bullets if none found
            return [
                "Developed scalable solutions, delivering measurable impact.",
                "Led cross-functional initiatives, resulting in improved performance.",
                "Optimized processes and systems, reducing costs and time."
            ]
        
        # Rewrite bullets
        rewritten = [self.rewrite_bullet(bullet) for bullet in bullets[:count]]
        
        # Ensure we have exactly 'count' bullets
        while len(rewritten) < count:
            # Generate a generic bullet
            rewritten.append("Delivered high-impact results, enabling scalable solutions.")
        
        return rewritten[:count]

