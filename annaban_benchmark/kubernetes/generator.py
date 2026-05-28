from typing import Dict


class K8sGenerator:
    def generate(self, benchmark_result: Dict) -> str:
        return f"""
apiVersion: batch/v1
kind: Job
metadata:
  name: annaban-governance-run
spec:
  template:
    spec:
      containers:
      - name: runner
        image: annaban/benchmark:latest
        env:
        - name: ANNABAN_GOVERNANCE_SCORE
          value: \"{benchmark_result['annaban_governance_score']}\"
        - name: ANNABAN_SCORE_NOTE
          value: \"operational metadata only; not truth validation\"
      restartPolicy: Never
""".strip()
