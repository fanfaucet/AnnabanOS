export const subscriptionModule = {
  checkQuota: async (usage) => ({ eligible: usage > 100, timestamp: Date.now(), usage }),
  streamQuotas: async function* () {
    while (true) {
      yield await subscriptionModule.checkQuota(Math.floor(Math.random() * 200));
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  },
};
