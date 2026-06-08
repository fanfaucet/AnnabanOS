#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ExecutionAuthority {
    Approved,
    Denied,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Telemetry {
    pub confidence: f32,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HapticOutput {
    pub frequency_hz: u16,
    pub intensity: f32,
    pub safe: bool,
}

pub struct HapticController {
    base_frequency_hz: f32,
    confidence_span_hz: f32,
}

impl Default for HapticController {
    fn default() -> Self {
        Self {
            base_frequency_hz: 50.0,
            confidence_span_hz: 200.0,
        }
    }
}

impl HapticController {
    pub fn map(&self, telemetry: Telemetry, authority: ExecutionAuthority) -> HapticOutput {
        if matches!(authority, ExecutionAuthority::Denied) {
            return HapticOutput {
                frequency_hz: 0,
                intensity: 0.0,
                safe: true,
            };
        }

        let confidence = telemetry.confidence.clamp(0.0, 1.0);
        HapticOutput {
            frequency_hz: (self.base_frequency_hz + confidence * self.confidence_span_hz).round() as u16,
            intensity: confidence,
            safe: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn approved_confidence_maps_to_operator_feedback() {
        let controller = HapticController::default();
        let output = controller.map(
            Telemetry { confidence: 0.81 },
            ExecutionAuthority::Approved,
        );

        assert_eq!(output.frequency_hz, 212);
        assert!((output.intensity - 0.81).abs() < f32::EPSILON);
        assert!(!output.safe);
    }

    #[test]
    fn denied_authority_forces_safe_output() {
        let controller = HapticController::default();
        let output = controller.map(
            Telemetry { confidence: 0.99 },
            ExecutionAuthority::Denied,
        );

        assert_eq!(output.frequency_hz, 0);
        assert_eq!(output.intensity, 0.0);
        assert!(output.safe);
    }
}
