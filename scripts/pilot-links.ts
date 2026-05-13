import os from "node:os";

type LinkSet = {
  host: string;
  api: string;
  pos: string;
  kds: string;
  qrTableT2: string;
  demo: string;
};

function getLanHosts() {
  const interfaces = os.networkInterfaces();
  const hosts = new Set<string>();

  for (const entries of Object.values(interfaces)) {
    for (const entry of entries ?? []) {
      if (entry.family === "IPv4" && !entry.internal) {
        hosts.add(entry.address);
      }
    }
  }

  return [...hosts];
}

function toLinks(host: string): LinkSet {
  return {
    host,
    api: `http://${host}:4000/health`,
    pos: `http://${host}:5173`,
    kds: `http://${host}:5174`,
    qrTableT2: `http://${host}:3000/table/T2`,
    demo: `http://${host}:5173/demo.html`
  };
}

const hosts = getLanHosts();
const links = hosts.map(toLinks);

console.log(
  JSON.stringify(
    {
      ok: links.length > 0,
      message: links.length > 0 ? "Use these URLs from devices on the same Wi-Fi/LAN" : "No LAN IPv4 address found",
      portsToAllow: [4000, 5173, 5174, 3000],
      links
    },
    null,
    2
  )
);

if (links.length === 0) {
  process.exitCode = 1;
}
