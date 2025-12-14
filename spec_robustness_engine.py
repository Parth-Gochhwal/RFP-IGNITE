import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from audit_logger import log_event


def awg_to_sqmm(awg_val: int) -> float:
	"""Approximate conversion from AWG to mm^2 using standard table values.
	The mapping covers common AWG sizes; for out-of-range inputs we approximate using an empirical formula.
	"""
	# lookup table for common AWG sizes (approx mm^2)
	awg_table = {
		0: 53.5, 1: 42.4, 2: 33.6, 3: 26.7, 4: 21.2, 5: 16.8, 6: 13.3,
		7: 10.55, 8: 8.37, 9: 6.63, 10: 5.26, 11: 4.17, 12: 3.31, 13: 2.62,
		14: 2.08, 15: 1.65, 16: 1.31, 17: 1.04, 18: 0.823, 19: 0.653, 20: 0.518,
		21: 0.41, 22: 0.326, 23: 0.258, 24: 0.205, 25: 0.162, 26: 0.129, 27: 0.102,
		28: 0.081, 29: 0.0642, 30: 0.0509, 31: 0.0404, 32: 0.0320, 33: 0.0254, 34: 0.0201,
		35: 0.0159, 36: 0.0126, 37: 0.0100, 38: 0.0080, 39: 0.0063, 40: 0.0050,
	}
	if awg_val in awg_table:
		return awg_table[awg_val]
	# empirical approximation for AWG > 40 or < 0 (rare): use standard formula
	try:
		# diameter (inches) = 0.0050 * 92 ** ((36 - AWG)/39)
		# area mm^2 = (pi/4) * (diameter_in_mm)^2
		import math

		diameter_inch = 0.005 * (92 ** ((36 - awg_val) / 39.0))
		diameter_mm = diameter_inch * 25.4
		area_mm2 = math.pi / 4.0 * (diameter_mm ** 2)
		return round(area_mm2, 4)
	except Exception:
		return 0.0


def convert_awg_to_sqmm(awg: int) -> Optional[float]:
	"""Deterministic conversion for common AWG values only.

	Supported AWG: 24, 20, 18, 16, 14, 12, 10
	Returns mm^2 as float for supported AWG, otherwise None.
	"""
	table = {
		24: 0.205,
		20: 0.518,
		18: 0.823,
		16: 1.31,
		14: 2.08,
		12: 3.31,
		10: 5.26,
	}
	return table.get(awg)


def write_robustness_log(rfp_id: str, line_item_id: Any, issue_type: str, raw_value: Any, action_taken: str, logs_dir: str = 'data/robustness_logs') -> bool:
	"""Append a robustness log entry to data/robustness_logs/{rfp_id}.json.

	The entry contains timestamp, rfp_id, line_item_id, issue_type, raw_value, action_taken.
	This function never raises; it returns True on success, False on failure.
	"""
	try:
		base_dir = os.path.join(os.path.dirname(__file__), os.pardir)
		# resolve logs directory relative to repository root
		logs_path = os.path.join(os.path.abspath(base_dir), logs_dir)
		os.makedirs(logs_path, exist_ok=True)
		file_path = os.path.join(logs_path, f"{rfp_id}.json")

		entry = {
			'timestamp': datetime.utcnow().isoformat() + 'Z',
			'rfp_id': rfp_id,
			'line_item_id': line_item_id,
			'issue_type': issue_type,
			'raw_value': raw_value,
			'action_taken': action_taken,
		}

		# load existing logs if present
		logs = []
		if os.path.exists(file_path):
			try:
				with open(file_path, 'r', encoding='utf-8') as fh:
					logs = json.load(fh) or []
			except Exception:
				# corrupt file or read error -> fallback to empty list
				logs = []

		logs.append(entry)
		# write back
		try:
			with open(file_path, 'w', encoding='utf-8') as fh:
				json.dump(logs, fh, indent=2, ensure_ascii=False)
		except Exception:
			return False
		return True
	except Exception:
		return False


def _find_in_text(pattern: str, text: str, flags=0):
	m = re.search(pattern, text, flags)
	return m.group(1).strip() if m else None


def _extract_units_from_text(text: str):
	"""Return list of (value, unit, raw_match) from free text for area/unit patterns."""
	results = []
	if not text:
		return results
	# match number + unit (mm2, mm², sqmm, AWG)
	patterns = [
		r"(\d+(?:\.\d+)?)\s*(?:mm2|mm\^2|mm²|sq\.?mm)\b",
		r"(AWG)\s*(\d{1,2})\b",
		r"(\d{1,2})\s*(?:AWG)\b",
	]
	for p in patterns:
		for m in re.finditer(p, text, flags=re.IGNORECASE):
			groups = m.groups()
			if not groups:
				continue
			# normalize
			raw = m.group(0)
			# cases
			if re.search(r"awg", raw, re.IGNORECASE):
				# extract AWG number
				num = None
				# patterns yield either (AWG, number) or (number, AWG)
				for g in groups[::-1]:
					if g and re.match(r"^\d+$", g):
						num = int(g)
						break
				if num is not None:
					results.append((num, 'AWG', raw))
			else:
				# numeric mm2 value
				val = float(groups[0])
				results.append((val, 'mm2', raw))
	return results


def run_spec_robustness_checks(rfp_id: str, parsed_rfp_data: dict) -> dict:
	"""Run deterministic robustness checks on parsed RFP data.

	Returns dict with keys:
	  - robustness_status: PASS / WARN / FAIL_SOFT
	  - missing_fields: mapping of line index -> list of missing fields
	  - unit_warnings: list of warnings about units and conversions
	  - fallback_applied: list of fallback extraction notes
	  - clarification_questions: list of questions for the user

	This function never raises; it captures exceptions and returns a FAIL_SOFT with diagnostic info.
	"""
	try:
		required_props = ['voltage_kV', 'core_count', 'conductor_material', 'insulation_material', 'armoured']

		unit_warnings = []
		fallback_applied = []
		missing_fields: Dict[int, List[str]] = {}
		clarification_questions = []

		# normalize line items
		items = []
		if isinstance(parsed_rfp_data, dict):
			if 'line_items' in parsed_rfp_data and isinstance(parsed_rfp_data['line_items'], list):
				items = parsed_rfp_data['line_items']
			elif 'items' in parsed_rfp_data and isinstance(parsed_rfp_data['items'], list):
				items = parsed_rfp_data['items']
			else:
				# maybe the passed dict is a single line item
				items = [parsed_rfp_data]
		elif isinstance(parsed_rfp_data, list):
			items = parsed_rfp_data
		else:
			items = [parsed_rfp_data]

		for idx, item in enumerate(items):
			try:
				item_missing = []
				# check basic fields
				for prop in required_props:
					if prop not in item or item.get(prop) in (None, '', []):
						item_missing.append(prop)

				# area: either 'area_sqmm' or field indicating AWG or 'area' with units
				area_present = False
				if 'area_sqmm' in item and item.get('area_sqmm') not in (None, ''):
					area_present = True
				if 'awg' in item and item.get('awg') not in (None, ''):
					area_present = True
				if 'area' in item and item.get('area') not in (None, ''):
					# try to interpret
					area_present = True

				if not area_present:
					item_missing.append('area_sqmm_or_awg')

				# attempt fallback extraction from text fields
				text_fields = []
				for k in ['description', 'notes', 'specs', 'full_text', 'details']:
					v = item.get(k)
					if isinstance(v, str) and v.strip():
						text_fields.append(v)
				text_blob = '\n'.join(text_fields)

				# fallback: voltage (kV)
				if 'voltage_kV' in item and item.get('voltage_kV') in (None, ''):
					v = _find_in_text(r"(\d+(?:\.\d+)?)\s*(?:kV|KV|kv)\b", text_blob, flags=re.IGNORECASE)
					if v:
						item['voltage_kV'] = float(v)
						fallback_applied.append(f"line_{idx}: set voltage_kV from text -> {v} kV")
						if 'voltage_kV' in item_missing:
							item_missing.remove('voltage_kV')

				# fallback: core_count
				if 'core_count' in item and item.get('core_count') in (None, ''):
					v = _find_in_text(r"(\d+)\s*(?:core|cores)\b", text_blob, flags=re.IGNORECASE)
					if v:
						item['core_count'] = int(v)
						fallback_applied.append(f"line_{idx}: set core_count from text -> {v}")
						if 'core_count' in item_missing:
							item_missing.remove('core_count')

				# fallback: conductor_material
				if 'conductor_material' in item and item.get('conductor_material') in (None, ''):
					v = _find_in_text(r"\b(copper|aluminium|aluminum|cu|al)\b", text_blob, flags=re.IGNORECASE)
					if v:
						normalized = v.lower()
						if normalized in ('cu', 'copper'):
							item['conductor_material'] = 'copper'
						elif normalized in ('aluminium', 'aluminum', 'al'):
							item['conductor_material'] = 'aluminium'
						else:
							item['conductor_material'] = normalized
						fallback_applied.append(f"line_{idx}: set conductor_material from text -> {item['conductor_material']}")
						if 'conductor_material' in item_missing:
							item_missing.remove('conductor_material')

				# fallback: insulation_material
				if 'insulation_material' in item and item.get('insulation_material') in (None, ''):
					v = _find_in_text(r"\b(xlpe|pvc|paper|pe|ptfe|silicone)\b", text_blob, flags=re.IGNORECASE)
					if v:
						item['insulation_material'] = v.lower()
						fallback_applied.append(f"line_{idx}: set insulation_material from text -> {item['insulation_material']}")
						if 'insulation_material' in item_missing:
							item_missing.remove('insulation_material')

				# fallback: armoured
				if 'armoured' in item and item.get('armoured') in (None, ''):
					if re.search(r"\b(armou?red|armour|armored)\b", text_blob, flags=re.IGNORECASE):
						item['armoured'] = True
						fallback_applied.append(f"line_{idx}: set armoured=True from text")
						if 'armoured' in item_missing:
							item_missing.remove('armoured')

				# fallback: area and units
				if 'area_sqmm' not in item or item.get('area_sqmm') in (None, ''):
					# search for mm2 or AWG in text_blob
					unit_matches = _extract_units_from_text(text_blob)
					if unit_matches:
						# pick first mm2 or AWG found deterministically
						picked = unit_matches[0]
						if picked[1] == 'mm2':
							item['area_sqmm'] = float(picked[0])
							fallback_applied.append(f"line_{idx}: set area_sqmm from text -> {picked[0]} mm2")
							if 'area_sqmm_or_awg' in item_missing:
								item_missing.remove('area_sqmm_or_awg')
						elif picked[1] == 'AWG':
							awg_num = int(picked[0])
							item['awg'] = awg_num
							conv = awg_to_sqmm(awg_num)
							item['area_sqmm'] = conv
							fallback_applied.append(f"line_{idx}: set awg from text -> AWG {awg_num} (~{conv} mm2)")
							unit_warnings.append(f"line_{idx}: AWG {awg_num} converted to {conv} mm2 (approx)")
							if 'area_sqmm_or_awg' in item_missing:
								item_missing.remove('area_sqmm_or_awg')

				# additional unit detection in explicit fields
				if 'area' in item and isinstance(item.get('area'), str):
					unit_matches = _extract_units_from_text(item['area'])
					if unit_matches:
						picked = unit_matches[0]
						if picked[1] == 'mm2':
							item['area_sqmm'] = float(picked[0])
							fallback_applied.append(f"line_{idx}: set area_sqmm from area field -> {picked[0]} mm2")
							if 'area_sqmm_or_awg' in item_missing:
								item_missing.remove('area_sqmm_or_awg')
						elif picked[1] == 'AWG':
							awg_num = int(picked[0])
							item['awg'] = awg_num
							conv = awg_to_sqmm(awg_num)
							item['area_sqmm'] = conv
							fallback_applied.append(f"line_{idx}: set awg from area field -> AWG {awg_num} (~{conv} mm2)")
							unit_warnings.append(f"line_{idx}: AWG {awg_num} converted to {conv} mm2 (approx)")
							if 'area_sqmm_or_awg' in item_missing:
								item_missing.remove('area_sqmm_or_awg')

				# ensure deterministic lists
				if item_missing:
					item_missing = sorted(set(item_missing))
					missing_fields[idx] = item_missing

			except Exception:
				# per-item exception should not stop overall processing
				missing_fields[idx] = missing_fields.get(idx, []) + ['processing_error']

		# derive status
		unresolved = any(v for v in missing_fields.values())
		if unresolved:
			robustness_status = 'FAIL_SOFT'
		else:
			if fallback_applied or unit_warnings:
				robustness_status = 'WARN'
			else:
				robustness_status = 'PASS'

		# build clarification questions for unresolved fields
		for idx, fields in sorted(missing_fields.items()):
			for f in fields:
				clarification_questions.append(f"Line item {idx}: please provide '{f}'")

		# deterministic ordering
		unit_warnings = sorted(set(unit_warnings))
		fallback_applied = sorted(set(fallback_applied))
		clarification_questions = sorted(set(clarification_questions))

		# attempt to write logs for events (never fail the check if logging fails)
		try:
			# log fallbacks
			for msg in fallback_applied:
				try:
					m = re.search(r"line_(\d+)", msg)
					line_id = int(m.group(1)) if m else None
					write_robustness_log(rfp_id, line_id, 'fallback', msg, msg)
				except Exception:
					pass

			# log unit warnings
			for msg in unit_warnings:
				try:
					m = re.search(r"line_(\d+)", msg)
					line_id = int(m.group(1)) if m else None
					write_robustness_log(rfp_id, line_id, 'unit_conversion', msg, msg)
				except Exception:
					pass

			# log missing fields as clarification requests
			for idx, fields in sorted(missing_fields.items()):
				try:
					for f in fields:
						write_robustness_log(rfp_id, idx, 'missing_field', f, 'requested_clarification')
				except Exception:
					pass
		except Exception:
			# ensure logging never breaks main flow
			pass

		result = {
			'robustness_status': robustness_status,
			'missing_fields': missing_fields,
			'unit_warnings': unit_warnings,
			'fallback_applied': fallback_applied,
			'clarification_questions': clarification_questions,
		}
		try:
			# audit summary (non-failing)
			log_event("spec_robustness_summary", {"rfp_id": rfp_id, "status": robustness_status, "missing_count": len(missing_fields)})
		except Exception:
			pass
		return result
	except Exception as e:
		# never raise; return a fail-soft with diagnostic
		return {
			'robustness_status': 'FAIL_SOFT',
			'missing_fields': {'global': ['exception_encountered']},
			'unit_warnings': [],
			'fallback_applied': [],
			'clarification_questions': [f'Processing error: {str(e)}'],
		}

