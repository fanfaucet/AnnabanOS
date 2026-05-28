from typing import Dict


class K8sGenerator:
    def generate(self, benchmark_result: Dict) -> str:
        return f"""
apiVersion: batch/v1
kind: Job
metadata:
  name: annaban-benchmark-run
spec:
  template:
    spec:
      containers:
      - name: runner
        image: annaban/benchmark:latest
        env:
        - name: SCORE
          value: \"{benchmark_result['annaban_governance_score']}\"
      restartPolicy: Never
""".strip()
