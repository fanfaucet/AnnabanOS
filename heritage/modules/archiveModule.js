export const archiveModule = {
  logMilestone: (milestone) => console.log("Archived:", { ...milestone, timestamp: Date.now() }),
  streamMilestones: async function* () {
    while (true) {
      yield null;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  },
};
