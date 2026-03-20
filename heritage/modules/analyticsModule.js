export const analyticsModule = {
  init: (userId) => {
    const session = { userId, events: [] };

    return {
      track: (type, data) => {
        session.events.push({ type, data, timestamp: Date.now() });
      },
      streamEvents: async function* () {
        for (const event of session.events) {
          yield event;
          await new Promise((resolve) => setTimeout(resolve, 10));
        }
      },
    };
  },
};
