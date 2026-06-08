import { runFictionalRtxSparkSession } from "./sparkIntegration.ts";

const result = runFictionalRtxSparkSession();
console.log(JSON.stringify(result, null, 2));
