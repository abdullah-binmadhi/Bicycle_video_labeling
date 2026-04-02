import yaml
import logging
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

# Configure basic logging for the loader
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@dataclass
class DataPaths:
    """Configuration for data directory paths."""
    sensor_data_dir: str
    processed_dir: str
    video_dir: str

@dataclass
class SensorRates:
    """Expected sampling frequencies (in Hz) for different modalities."""
    imu_hz: int
    gnss_hz: int
    video_hz: int
    lidar_hz: int

@dataclass
class Hyperparameters:
    """Training and data window hyperparameters."""
    batch_size: int
    learning_rate: float
    epochs: int
    sequence_length: int

@dataclass
class ModelSettings:
    """Feature flags and architecture configurations for the models."""
    use_vision: bool
    use_imu: bool
    use_lidar: bool
    imu_features: int
    num_classes: int

@dataclass
class FrameworkConfig:
    """Root configuration object containing all framework settings."""
    data_paths: DataPaths
    sensor_rates: SensorRates
    hyperparameters: Hyperparameters
    model_settings: ModelSettings

def load_config(config_path: str | Path = "config.yaml") -> FrameworkConfig:
    """
    Loads and parses the YAML configuration file into strongly-typed dataclasses.
    
    This ensures that the IDE provides autocomplete and type warnings, 
    preventing typos or runtime errors when accessing config variables.

    Args:
        config_path (str | Path): Path to the YAML configuration file.

    Returns:
        FrameworkConfig: A fully instantiated configuration object.
        
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
        KeyError: If required configuration sections are missing.
    """
    path = Path(config_path)
    if not path.is_file():
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Missing config file at {config_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data: Dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logging.error(f"Failed to parse YAML file: {e}")
        raise

    try:
        # Instantiate dataclasses with parsed dictionary sections
        paths = DataPaths(**raw_data["data_paths"])
        rates = SensorRates(**raw_data["sensor_rates"])
        hyperparams = Hyperparameters(**raw_data["hyperparameters"])
        settings = ModelSettings(**raw_data["model_settings"])
    except TypeError as e:
        logging.error(f"Missing or mismatched configuration keys: {e}")
        raise KeyError(f"Invalid configuration schema in {config_path}: {e}")

    logging.info(f"Successfully loaded configuration from {config_path}")
    return FrameworkConfig(
        data_paths=paths,
        sensor_rates=rates,
        hyperparameters=hyperparams,
        model_settings=settings
    )

if __name__ == "__main__":
    # Test execution
    try:
        cfg = load_config("config.yaml")
        print("\nConfig loaded dynamically. Example usage autocomplete: ")
        print(f"- Batch Size: {cfg.hyperparameters.batch_size}")
        print(f"- Use Vision Models: {cfg.model_settings.use_vision}")
        print(f"- Output Directory: {cfg.data_paths.processed_dir}")
    except Exception as e:
        print(f"Error loading config: {e}")
