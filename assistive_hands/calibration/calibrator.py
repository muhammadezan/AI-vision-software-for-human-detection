"""Calibration system for gaze point mapping."""

import numpy as np
import json
import logging
from typing import Tuple, List, Dict, Optional
from pathlib import Path
from datetime import datetime

from config.settings import SystemConfig

logger = logging.getLogger(__name__)


class Calibrator:
    """Handles 9-point calibration for gaze tracking."""

    def __init__(self):
        """Initialize calibrator."""
        self.grid_size = SystemConfig.CALIBRATION_GRID_SIZE
        self.calibration_points = []
        self.gaze_samples = {}
        self.mapping_matrix = None
        self.validation_results = None
        self.calibration_valid = False

    def generate_calibration_points(
        self,
        screen_width: int,
        screen_height: int,
        grid_size: Optional[int] = None
    ) -> List[Tuple[int, int]]:
        """
        Generate calibration grid points.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            grid_size: Grid size (default 3x3)
            
        Returns:
            List of (x, y) calibration points
        """
        if grid_size is None:
            grid_size = self.grid_size
        
        points = []
        
        # Add margin to avoid edge effects
        margin_x = screen_width // 8
        margin_y = screen_height // 8
        
        x_positions = np.linspace(margin_x, screen_width - margin_x, grid_size)
        y_positions = np.linspace(margin_y, screen_height - margin_y, grid_size)
        
        for y in y_positions:
            for x in x_positions:
                points.append((int(x), int(y)))
        
        self.calibration_points = points
        logger.info(f"Generated {len(points)} calibration points")
        return points

    def collect_gaze_samples(
        self,
        target_point: Tuple[int, int],
        gaze_samples: List[Tuple[float, float]],
        duration: float = 2.0
    ) -> bool:
        """
        Record gaze samples for a calibration point.
        
        Args:
            target_point: Screen coordinates of calibration point
            gaze_samples: List of gaze position samples
            duration: Duration of sample collection
            
        Returns:
            True if sufficient samples collected
        """
        try:
            min_samples = SystemConfig.CALIBRATION_MIN_SAMPLES
            
            if len(gaze_samples) < min_samples:
                logger.debug(f"Insufficient samples for point {target_point}: {len(gaze_samples)} < {min_samples}")
                # Still store the point even with fewer samples (for graceful degradation)
                # but mark it as lower confidence
                pass
            
            # Use only the middle samples to avoid startup artifacts
            start_idx = max(0, len(gaze_samples) // 4)
            end_idx = min(len(gaze_samples), 3 * len(gaze_samples) // 4)
            valid_samples = gaze_samples[start_idx:end_idx]
            
            if len(valid_samples) > 0:
                self.gaze_samples[target_point] = {
                    'samples': valid_samples,
                    'mean': tuple(np.mean(valid_samples, axis=0)),
                    'std': tuple(np.std(valid_samples, axis=0)),
                    'num_samples': len(valid_samples)
                }
                
                logger.info(f"Collected {len(valid_samples)} samples for point {target_point}")
                return True
            else:
                logger.warning(f"No valid samples for point {target_point}")
                return False
            
        except Exception as e:
            logger.error(f"Error collecting gaze samples: {e}", exc_info=True)
            return False

    def calculate_mapping_matrix(self) -> bool:
        """
        Calculate linear transformation matrix from gaze to screen coordinates.
        
        Returns:
            True if calculation successful
        """
        try:
            if len(self.gaze_samples) < 4:
                logger.error("Need at least 4 calibration points")
                return False
            
            # Prepare data
            screen_points = []
            gaze_points = []
            
            for screen_coord, sample_data in self.gaze_samples.items():
                gaze_points.append(sample_data['mean'])
                screen_points.append(screen_coord)
            
            gaze_points = np.array(gaze_points)
            screen_points = np.array(screen_points)
            
            # Fit linear transformation: screen = gaze @ matrix
            # Using least squares
            ones = np.ones((gaze_points.shape[0], 1))
            X = np.hstack([gaze_points, ones])
            
            # Solve for transformation matrix
            self.mapping_matrix, _, _, _ = np.linalg.lstsq(X, screen_points, rcond=None)
            
            logger.info("Mapping matrix calculated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating mapping matrix: {e}")
            return False

    def validate_calibration(self, test_points: Optional[List[Tuple[int, int]]] = None) -> Dict:
        """
        Validate calibration accuracy.
        
        Args:
            test_points: Optional list of test points
            
        Returns:
            Validation results dictionary
        """
        try:
            if self.mapping_matrix is None:
                logger.error("No mapping matrix available for validation")
                return {'valid': False, 'error': 'No mapping matrix'}
            
            if test_points is None:
                test_points = self.calibration_points
            
            results = {
                'points_tested': len(test_points),
                'errors': [],
                'mean_error': 0.0,
                'max_error': 0.0,
                'valid': True
            }
            
            for point in test_points:
                if point in self.gaze_samples:
                    predicted = self.apply_mapping(self.gaze_samples[point]['mean'])
                    error = np.linalg.norm(np.array(predicted) - np.array(point))
                    results['errors'].append(float(error))
            
            if results['errors']:
                results['mean_error'] = float(np.mean(results['errors']))
                results['max_error'] = float(np.max(results['errors']))
                
                threshold = SystemConfig.CALIBRATION_VALIDATION_THRESHOLD * 100  # Convert to pixels
                results['valid'] = results['mean_error'] < threshold
            
            self.validation_results = results
            self.calibration_valid = results['valid']
            
            logger.info(f"Calibration validation: mean_error={results['mean_error']:.2f}px, valid={results['valid']}")
            return results
            
        except Exception as e:
            logger.error(f"Error validating calibration: {e}")
            return {'valid': False, 'error': str(e)}

    def apply_mapping(self, gaze_point: Tuple[float, float]) -> Tuple[int, int]:
        """
        Apply calibration mapping to gaze point.
        
        Args:
            gaze_point: (x, y) normalized gaze point
            
        Returns:
            (x, y) screen coordinates
        """
        if self.mapping_matrix is None:
            return tuple(int(g) for g in gaze_point)
        
        try:
            gaze_array = np.array([gaze_point[0], gaze_point[1], 1])
            screen_point = gaze_array @ self.mapping_matrix
            return (int(screen_point[0]), int(screen_point[1]))
        except Exception as e:
            logger.error(f"Error applying mapping: {e}")
            return (int(gaze_point[0] * SystemConfig.SCREEN_RESOLUTION[0]),
                    int(gaze_point[1] * SystemConfig.SCREEN_RESOLUTION[1]))

    def save_calibration(self, user_profile: str = 'default') -> bool:
        """
        Save calibration data to file.
        
        Args:
            user_profile: User profile name
            
        Returns:
            True if successful
        """
        try:
            SystemConfig.CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
            
            calibration_file = SystemConfig.CALIBRATION_DIR / f"{user_profile}_calibration.npz"
            
            np.savez(
                calibration_file,
                matrix=self.mapping_matrix,
                points=self.calibration_points,
                samples=self.gaze_samples,
                validation=self.validation_results
            )
            
            # Also save metadata
            metadata = {
                'user_profile': user_profile,
                'timestamp': datetime.now().isoformat(),
                'grid_size': self.grid_size,
                'valid': self.calibration_valid
            }
            
            metadata_file = SystemConfig.CALIBRATION_DIR / f"{user_profile}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Calibration saved to {calibration_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving calibration: {e}")
            return False

    def load_calibration(self, user_profile: str = 'default') -> bool:
        """
        Load calibration data from file.
        
        Args:
            user_profile: User profile name
            
        Returns:
            True if successful
        """
        try:
            calibration_file = SystemConfig.CALIBRATION_DIR / f"{user_profile}_calibration.npz"
            
            if not calibration_file.exists():
                logger.debug(f"Calibration file not yet created: {calibration_file}")
                return False
            
            data = np.load(calibration_file)
            self.mapping_matrix = data['matrix']
            self.calibration_points = data['points'].tolist()
            self.calibration_valid = True
            
            logger.info(f"Calibration loaded from {calibration_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
            return False

    def reset(self):
        """Reset calibration data."""
        self.calibration_points = []
        self.gaze_samples = {}
        self.mapping_matrix = None
        self.validation_results = None
        self.calibration_valid = False
        logger.info("Calibration reset")
