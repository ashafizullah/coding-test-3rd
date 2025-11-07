"""
Table Parser Service

Extracts and classifies tables from PDF documents for fund performance analysis.
Handles capital calls, distributions, and adjustments tables.
"""

import re
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import pdfplumber
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class TableParser:
    """Parser for extracting structured data from PDF tables"""

    # Keywords for table classification
    CAPITAL_CALL_KEYWORDS = ['capital call', 'call number', 'capital contribution', 'capital drawdown']
    DISTRIBUTION_KEYWORDS = ['distribution', 'return of capital', 'dividend', 'recallable']
    ADJUSTMENT_KEYWORDS = ['adjustment', 'rebalance', 'recalled distribution', 'capital call adjustment']

    def __init__(self):
        """Initialize the table parser"""
        self.llm_client = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM client for text-based extraction"""
        try:
            if settings.LLM_PROVIDER == "groq":
                from groq import Groq
                self.llm_client = Groq(api_key=settings.GROQ_API_KEY)
                self.llm_model = settings.GROQ_MODEL
            elif settings.LLM_PROVIDER == "openai":
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.llm_model = settings.OPENAI_MODEL
            logger.info(f"Initialized LLM client: {settings.LLM_PROVIDER}")
        except Exception as e:
            logger.warning(f"Could not initialize LLM for text extraction: {e}")

    def extract_data_from_text(self, pdf_path: str) -> Dict[str, List[Dict]]:
        """
        Extract capital calls and distributions from PDF text using LLM.

        This is a fallback method when structured tables are not found.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with 'capital_calls' and 'distributions' lists
        """
        if not self.llm_client:
            logger.warning("LLM client not available for text extraction")
            return {'capital_calls': [], 'distributions': [], 'adjustments': []}

        try:
            # Extract all text from PDF
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"

            if not full_text.strip():
                logger.warning("No text found in PDF")
                return {'capital_calls': [], 'distributions': [], 'adjustments': []}

            # Use LLM to extract structured data
            prompt = f"""Extract fund performance data from the following text.

Find all capital calls and distributions mentioned in the text.

For each capital call, extract:
- date (in YYYY-MM-DD format)
- amount (numeric only, without currency symbols)
- purpose/description

For each distribution, extract:
- date (in YYYY-MM-DD format)
- amount (numeric only, without currency symbols)
- type (e.g., "Distribution", "Return of Capital")
- description

Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
{{
  "capital_calls": [
    {{"date": "2025-05-01", "amount": 5000000, "call_type": "Standard Call", "description": "Follow-on investment"}},
    ...
  ],
  "distributions": [
    {{"date": "2025-03-15", "amount": 2000000, "distribution_type": "Distribution", "description": "Q1 2025 distribution"}},
    ...
  ]
}}

Text:
{full_text[:8000]}"""

            # Call LLM
            if settings.LLM_PROVIDER == "groq":
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content
            elif settings.LLM_PROVIDER == "openai":
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content

            # Parse JSON response
            # Remove markdown code blocks if present
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            data = json.loads(result_text)

            # Convert to expected format
            capital_calls = []
            for cc in data.get('capital_calls', []):
                try:
                    capital_calls.append({
                        'call_date': self._parse_date(cc.get('date')),
                        'call_type': cc.get('call_type', 'Standard Call'),
                        'amount': Decimal(str(cc.get('amount', 0))),
                        'description': cc.get('description', '')
                    })
                except Exception as e:
                    logger.warning(f"Error parsing capital call from LLM: {e}")

            distributions = []
            for dist in data.get('distributions', []):
                try:
                    distributions.append({
                        'distribution_date': self._parse_date(dist.get('date')),
                        'distribution_type': dist.get('distribution_type', 'Distribution'),
                        'amount': Decimal(str(dist.get('amount', 0))),
                        'is_recallable': False,
                        'description': dist.get('description', '')
                    })
                except Exception as e:
                    logger.warning(f"Error parsing distribution from LLM: {e}")

            logger.info(f"LLM extracted {len(capital_calls)} capital calls and {len(distributions)} distributions from text")
            return {
                'capital_calls': capital_calls,
                'distributions': distributions,
                'adjustments': []
            }

        except Exception as e:
            logger.error(f"Error extracting data from text using LLM: {e}")
            return {'capital_calls': [], 'distributions': [], 'adjustments': []}

    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract all tables from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of dictionaries containing table data and metadata
        """
        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract tables from the page
                    page_tables = page.extract_tables()

                    if not page_tables:
                        continue

                    for table_num, table_data in enumerate(page_tables, start=1):
                        if not table_data or len(table_data) < 2:  # Need at least header + 1 row
                            continue

                        table_info = {
                            'page': page_num,
                            'table_number': table_num,
                            'raw_data': table_data,
                            'headers': table_data[0] if table_data else [],
                            'rows': table_data[1:] if len(table_data) > 1 else []
                        }

                        tables.append(table_info)

            logger.info(f"Extracted {len(tables)} tables from PDF: {pdf_path}")
            return tables

        except Exception as e:
            logger.error(f"Error extracting tables from PDF {pdf_path}: {e}")
            raise

    def classify_table_type(self, table_info: Dict) -> Optional[str]:
        """
        Classify the type of table based on headers and content.

        Args:
            table_info: Dictionary containing table data and headers

        Returns:
            Table type: 'capital_calls', 'distributions', 'adjustments', or None
        """
        # Get headers and first few rows as text
        headers = table_info.get('headers', [])
        rows = table_info.get('rows', [])[:5]  # Check first 5 rows

        # Combine for keyword matching (case-insensitive)
        text_to_check = ' '.join([
            ' '.join(str(h) for h in headers if h),
            ' '.join(' '.join(str(cell) for cell in row if cell) for row in rows)
        ]).lower()

        # Classification logic
        if any(keyword in text_to_check for keyword in self.CAPITAL_CALL_KEYWORDS):
            return 'capital_calls'
        elif any(keyword in text_to_check for keyword in self.DISTRIBUTION_KEYWORDS):
            return 'distributions'
        elif any(keyword in text_to_check for keyword in self.ADJUSTMENT_KEYWORDS):
            return 'adjustments'

        logger.warning(f"Could not classify table with headers: {headers}")
        return None

    def parse_capital_call_table(self, table_info: Dict) -> List[Dict]:
        """
        Parse a capital call table into structured data.

        Expected columns: Date, Call Number, Amount, Description

        Args:
            table_info: Dictionary containing table data

        Returns:
            List of dictionaries with parsed capital call data
        """
        results = []
        headers = [str(h).strip().lower() if h else '' for h in table_info['headers']]
        rows = table_info['rows']

        # Find column indices
        date_idx = self._find_column_index(headers, ['date'])
        amount_idx = self._find_column_index(headers, ['amount'])
        call_type_idx = self._find_column_index(headers, ['call number', 'type', 'call'])
        description_idx = self._find_column_index(headers, ['description', 'desc', 'notes'])

        for row in rows:
            if not row or len(row) == 0:
                continue

            # Skip empty rows
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            try:
                call_data = {
                    'call_date': self._parse_date(row[date_idx] if date_idx is not None else None),
                    'call_type': str(row[call_type_idx]).strip() if call_type_idx is not None and row[call_type_idx] else 'Standard Call',
                    'amount': self._parse_amount(row[amount_idx] if amount_idx is not None else None),
                    'description': str(row[description_idx]).strip() if description_idx is not None and row[description_idx] else ''
                }

                # Validate required fields
                if call_data['call_date'] and call_data['amount'] is not None:
                    results.append(call_data)
                else:
                    logger.warning(f"Skipping invalid capital call row: {row}")

            except Exception as e:
                logger.warning(f"Error parsing capital call row {row}: {e}")
                continue

        logger.info(f"Parsed {len(results)} capital call entries")
        return results

    def parse_distribution_table(self, table_info: Dict) -> List[Dict]:
        """
        Parse a distribution table into structured data.

        Expected columns: Date, Type, Amount, Recallable, Description

        Args:
            table_info: Dictionary containing table data

        Returns:
            List of dictionaries with parsed distribution data
        """
        results = []
        headers = [str(h).strip().lower() if h else '' for h in table_info['headers']]
        rows = table_info['rows']

        # Find column indices
        date_idx = self._find_column_index(headers, ['date'])
        amount_idx = self._find_column_index(headers, ['amount'])
        type_idx = self._find_column_index(headers, ['type', 'distribution type'])
        recallable_idx = self._find_column_index(headers, ['recallable', 'recall'])
        description_idx = self._find_column_index(headers, ['description', 'desc', 'notes'])

        for row in rows:
            if not row or len(row) == 0:
                continue

            # Skip empty rows
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            try:
                dist_data = {
                    'distribution_date': self._parse_date(row[date_idx] if date_idx is not None else None),
                    'distribution_type': str(row[type_idx]).strip() if type_idx is not None and row[type_idx] else 'Distribution',
                    'amount': self._parse_amount(row[amount_idx] if amount_idx is not None else None),
                    'is_recallable': self._parse_boolean(row[recallable_idx] if recallable_idx is not None else 'No'),
                    'description': str(row[description_idx]).strip() if description_idx is not None and row[description_idx] else ''
                }

                # Validate required fields
                if dist_data['distribution_date'] and dist_data['amount'] is not None:
                    results.append(dist_data)
                else:
                    logger.warning(f"Skipping invalid distribution row: {row}")

            except Exception as e:
                logger.warning(f"Error parsing distribution row {row}: {e}")
                continue

        logger.info(f"Parsed {len(results)} distribution entries")
        return results

    def parse_adjustment_table(self, table_info: Dict) -> List[Dict]:
        """
        Parse an adjustment table into structured data.

        Expected columns: Date, Type, Amount, Description

        Args:
            table_info: Dictionary containing table data

        Returns:
            List of dictionaries with parsed adjustment data
        """
        results = []
        headers = [str(h).strip().lower() if h else '' for h in table_info['headers']]
        rows = table_info['rows']

        # Find column indices
        date_idx = self._find_column_index(headers, ['date'])
        amount_idx = self._find_column_index(headers, ['amount'])
        type_idx = self._find_column_index(headers, ['type', 'adjustment type'])
        description_idx = self._find_column_index(headers, ['description', 'desc', 'notes'])

        for row in rows:
            if not row or len(row) == 0:
                continue

            # Skip empty rows
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            try:
                adj_type = str(row[type_idx]).strip().lower() if type_idx is not None and row[type_idx] else ''

                # Determine category and if it's a contribution adjustment
                category = self._classify_adjustment_category(adj_type)
                is_contribution_adjustment = 'capital call' in adj_type or 'contribution' in adj_type

                adj_data = {
                    'adjustment_date': self._parse_date(row[date_idx] if date_idx is not None else None),
                    'adjustment_type': str(row[type_idx]).strip() if type_idx is not None and row[type_idx] else 'Adjustment',
                    'category': category,
                    'amount': self._parse_amount(row[amount_idx] if amount_idx is not None else None),
                    'is_contribution_adjustment': is_contribution_adjustment,
                    'description': str(row[description_idx]).strip() if description_idx is not None and row[description_idx] else ''
                }

                # Validate required fields
                if adj_data['adjustment_date'] and adj_data['amount'] is not None:
                    results.append(adj_data)
                else:
                    logger.warning(f"Skipping invalid adjustment row: {row}")

            except Exception as e:
                logger.warning(f"Error parsing adjustment row {row}: {e}")
                continue

        logger.info(f"Parsed {len(results)} adjustment entries")
        return results

    def validate_and_clean_data(self, data: List[Dict], table_type: str) -> List[Dict]:
        """
        Validate and clean parsed data.

        Args:
            data: List of parsed data dictionaries
            table_type: Type of table ('capital_calls', 'distributions', 'adjustments')

        Returns:
            Cleaned and validated data
        """
        cleaned_data = []

        for entry in data:
            try:
                # Check required fields based on table type
                if table_type == 'capital_calls':
                    if not entry.get('call_date') or entry.get('amount') is None:
                        continue
                    if entry['amount'] <= 0:
                        logger.warning(f"Capital call with non-positive amount: {entry}")

                elif table_type == 'distributions':
                    if not entry.get('distribution_date') or entry.get('amount') is None:
                        continue
                    if entry['amount'] <= 0:
                        logger.warning(f"Distribution with non-positive amount: {entry}")

                elif table_type == 'adjustments':
                    if not entry.get('adjustment_date') or entry.get('amount') is None:
                        continue
                    # Adjustments can be positive or negative

                cleaned_data.append(entry)

            except Exception as e:
                logger.warning(f"Error validating entry {entry}: {e}")
                continue

        logger.info(f"Validated {len(cleaned_data)}/{len(data)} {table_type} entries")
        return cleaned_data

    # Helper methods

    def _find_column_index(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """
        Find the index of a column by matching keywords in headers.

        Args:
            headers: List of header strings (lowercase)
            keywords: List of keywords to match

        Returns:
            Index of the matching column, or None if not found
        """
        for idx, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return idx
        return None

    def _parse_date(self, date_str: any) -> Optional[datetime]:
        """
        Parse date from various formats.

        Supports: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.

        Args:
            date_str: Date string or object

        Returns:
            datetime object or None if parsing fails
        """
        if date_str is None:
            return None

        if isinstance(date_str, datetime):
            return date_str

        date_str = str(date_str).strip()

        if not date_str:
            return None

        # Try different date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y%m%d'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _parse_amount(self, amount_str: any) -> Optional[Decimal]:
        """
        Parse monetary amount from string.

        Handles: $1,000,000 | 1000000 | ($500,000) | -$500,000

        Args:
            amount_str: Amount string or number

        Returns:
            Decimal amount or None if parsing fails
        """
        if amount_str is None:
            return None

        # If already a number
        if isinstance(amount_str, (int, float, Decimal)):
            return Decimal(str(amount_str))

        amount_str = str(amount_str).strip()

        if not amount_str:
            return None

        # Check if amount is in parentheses (negative)
        is_negative = amount_str.startswith('(') and amount_str.endswith(')')

        # Remove currency symbols, commas, parentheses
        amount_str = re.sub(r'[$,()]', '', amount_str)

        # Handle negative sign
        if amount_str.startswith('-'):
            is_negative = True
            amount_str = amount_str[1:]

        try:
            amount = Decimal(amount_str)
            return -amount if is_negative else amount
        except Exception as e:
            logger.warning(f"Could not parse amount: {amount_str} - {e}")
            return None

    def _parse_boolean(self, value: any) -> bool:
        """
        Parse boolean value from various formats.

        Args:
            value: Value to parse (Yes/No, True/False, 1/0, etc.)

        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        value_str = str(value).strip().lower()

        return value_str in ['yes', 'true', '1', 'y', 't']

    def _classify_adjustment_category(self, adjustment_type: str) -> str:
        """
        Classify adjustment into category.

        Args:
            adjustment_type: Type of adjustment (lowercase)

        Returns:
            Category string
        """
        if 'recallable' in adjustment_type or 'recalled' in adjustment_type:
            return 'recallable_distribution'
        elif 'capital call' in adjustment_type:
            return 'capital_call_adjustment'
        elif 'contribution' in adjustment_type:
            return 'contribution_adjustment'
        elif 'fee' in adjustment_type:
            return 'fee_adjustment'
        elif 'expense' in adjustment_type:
            return 'expense_adjustment'
        else:
            return 'other'
