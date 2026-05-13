const checks = [
  {
    name: "api",
    url: "http://127.0.0.1:4000/health"
  },
  {
    name: "pos",
    url: "http://127.0.0.1:5173"
  },
  {
    name: "kds",
    url: "http://127.0.0.1:5174"
  },
  {
    name: "qr",
    url: "http://127.0.0.1:3000"
  }
];

async function main() {
  const results = await Promise.all(
    checks.map(async (check) => {
      try {
        const response = await fetch(check.url);

        return {
          name: check.name,
          url: check.url,
          ok: response.ok,
          status: response.status
        };
      } catch (error) {
        return {
          name: check.name,
          url: check.url,
          ok: false,
          status: 0,
          error: error instanceof Error ? error.message : "Unknown error"
        };
      }
    })
  );

  const ok = results.every((result) => result.ok);

  console.log(
    JSON.stringify(
      {
        ok,
        results
      },
      null,
      2
    )
  );

  if (!ok) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
