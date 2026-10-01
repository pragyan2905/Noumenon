import time
import tempfile
import shutil
import json
import csv
from pathlib import Path

# Optional dependencies for formats other than JSON/CSV/TSV
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class DataEngine(ConversionEngine):
    """
    Handles robust tabular/structured data conversions.
    Supports JSON, CSV, TSV natively. YAML and TOML if libraries are present.
    """
    
    def __init__(self):
        self.formats = {'json', 'csv', 'tsv'}
        if HAS_YAML:
            self.formats.update({'yaml', 'yml'})
        if HAS_TOML:
            self.formats.add('toml')
        if HAS_PANDAS:
            self.formats.update({'xlsx', 'parquet'})

    def can_convert(self, source_format: str, target_format: str) -> bool:
        return source_format in self.formats and target_format in self.formats

    def get_quality_score(self) -> str:
        return 'A'

    def _read_data(self, path: Path, ext: str):
        with open(path, 'r', encoding='utf-8') as f:
            if ext == 'json':
                return json.load(f)
            elif ext == 'yaml' or ext == 'yml':
                return yaml.safe_load(f)
            elif ext == 'toml':
                return toml.load(f)
            elif ext in ('csv', 'tsv'):
                delimiter = '\t' if ext == 'tsv' else ','
                reader = csv.DictReader(f, delimiter=delimiter)
                return [row for row in reader]
        
        # Binary formats handled by pandas
        if HAS_PANDAS and ext in ('xlsx', 'parquet'):
            if ext == 'xlsx':
                df = pd.read_excel(path)
            else:
                df = pd.read_parquet(path)
            return df.to_dict('records')
            
        raise ValueError(f"Unsupported read format: {ext}")

    def _write_data(self, data, path: Path, ext: str):
        with open(path, 'w', encoding='utf-8') as f:
            if ext == 'json':
                json.dump(data, f, indent=2)
            elif ext == 'yaml' or ext == 'yml':
                yaml.dump(data, f, default_flow_style=False)
            elif ext == 'toml':
                toml.dump(data, f)
            elif ext in ('csv', 'tsv'):
                delimiter = '\t' if ext == 'tsv' else ','
                
                # If data is a dict (e.g. from JSON), we try to convert it to a list of dicts or list of lists
                # If it's a list of dicts:
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    keys = list(data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=keys, delimiter=delimiter)
                    writer.writeheader()
                    writer.writerows(data)
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    writer = csv.writer(f, delimiter=delimiter)
                    writer.writerows(data)
                elif isinstance(data, dict):
                    # Flatten simple dict to 2 columns (key, value)
                    writer = csv.writer(f, delimiter=delimiter)
                    writer.writerow(["key", "value"])
                    for k, v in data.items():
                        # stringify complex values
                        writer.writerow([k, json.dumps(v) if isinstance(v, (dict, list)) else v])
                else:
                    raise ValueError(f"Data structure not suitable for {ext.upper()} conversion.")
            else:
                if HAS_PANDAS and ext in ('xlsx', 'parquet'):
                    pass # Handled outside the with block
                else:
                    raise ValueError(f"Unsupported write format: {ext}")

        # Handle binary writes
        if HAS_PANDAS and ext in ('xlsx', 'parquet'):
            # Convert list of dicts to dataframe
            if isinstance(data, dict):
                df = pd.DataFrame(list(data.items()), columns=['key', 'value'])
                # Convert complex values to strings for parquet/excel compatibility
                df['value'] = df['value'].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            elif isinstance(data, list):
                # Ensure all complex dicts/lists inside the main list are strings for parquet
                processed_data = []
                for row in data:
                    if isinstance(row, dict):
                        processed_data.append({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
                    else:
                        processed_data.append(row)
                df = pd.DataFrame(processed_data)
            else:
                raise ValueError(f"Data structure not suitable for {ext.upper()} conversion.")
                
            if ext == 'xlsx':
                df.to_excel(path, index=False)
            else:
                # Parquet requires string column names
                df.columns = df.columns.astype(str)
                df.to_parquet(path, index=False)

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            # Read input
            try:
                data = self._read_data(request.input_path, source_ext)
            except Exception as e:
                return ConversionResult(success=False, error_message=f"Failed to read {source_ext.upper()}: {str(e)}")
            
            # Write temp output
            fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
            import os
            os.close(fd)
            temp_out = Path(temp_out_path)
            
            try:
                self._write_data(data, temp_out, target_ext)
                
                # Verify generated output by reading it back
                try:
                    self._read_data(temp_out, target_ext)
                except Exception as e:
                    raise ValueError(f"Generated output verification failed: {str(e)}")
                
                output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
                shutil.move(str(temp_out), str(output_path))
                
            except Exception as e:
                if temp_out.exists():
                    temp_out.unlink()
                raise e
                
            return ConversionResult(
                success=True,
                output_path=output_path,
                engine_used=self.__class__.__name__,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"Data conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
