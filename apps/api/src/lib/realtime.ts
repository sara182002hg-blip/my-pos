import { appRepository } from "../data/app-state";

type LiveClient = {
  send: (payload: string) => void;
  on: (event: string, handler: () => void) => void;
};

const liveClients = new Set<LiveClient>();

export const broadcastSnapshot = () => {
  const payload = JSON.stringify({
    type: "snapshot",
    payload: appRepository.getSnapshot()
  });

  for (const client of liveClients) {
    client.send(payload);
  }
};

export const registerLiveSocket = (socket: LiveClient) => {
  liveClients.add(socket);
  socket.send(
    JSON.stringify({
      type: "snapshot",
      payload: appRepository.getSnapshot()
    })
  );

  const interval = setInterval(() => {
    socket.send(
      JSON.stringify({
        type: "heartbeat",
        payload: {
          now: new Date().toISOString()
        }
      })
    );
  }, 15000);

  socket.on("close", () => {
    liveClients.delete(socket);
    clearInterval(interval);
  });
};
