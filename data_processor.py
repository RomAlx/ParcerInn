import logging
from datetime import datetime
from typing import Dict, List, Tuple, Set

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        self.current_date = datetime.now().strftime("%d.%m.%Y")

    def process(self, inn: str, pdf_data: Dict, current_data: Dict) -> Dict:
        try:
            logger.info(f"Processing data for INN: {inn}")

            new_founders = self._parse_founders(pdf_data.get('founders', []))
            current_founders = self._parse_founders(current_data.get('current_founders', ''))
            former_founders = self._parse_founders(current_data.get('former_founders', ''))

            added_founders, removed_founders = self._compare_founders(current_founders, new_founders)

            change_date = pdf_data.get('latest_date')

            updated_data = {
                'name': pdf_data.get('short_name', current_data.get('name', '')),
                'current_founders': self._format_founders(new_founders),
                'former_founders': self._format_founders(removed_founders),
                'change_date': change_date
            }

            logger.info(f"Processed data for INN {inn}: {updated_data}")
            return updated_data
        except Exception as e:
            logger.error(f"Error processing data for INN {inn}: {str(e)}", exc_info=True)
            return current_data

    def _parse_founders(self, founders_data) -> Set[str]:
        if isinstance(founders_data, list):
            return set(f"{' '.join(founder['name']).title()} - {founder['inn']} - {founder['latest_date']}" for founder in founders_data)
        elif isinstance(founders_data, str):
            return set(founder.strip() for founder in founders_data.split('\n') if founder.strip())
        return set()

    def _format_founders(self, founders: Set[str]) -> str:
        return '\n'.join(sorted(founders))

    def _compare_founders(self, current: Set[str], new: Set[str]) -> Tuple[Set[str], Set[str]]:
        added = new - current
        removed = current - new
        return added, removed
