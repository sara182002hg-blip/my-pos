"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export default function PwaInstall() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(false);
  const [message, setMessage] = useState("ติดตั้งเป็นแอพได้จากเมนู browser");

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        setMessage("เปิดแบบเว็บได้ตามปกติ");
      });
    }

    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as BeforeInstallPromptEvent);
      setMessage("พร้อมติดตั้งเป็นแอพ");
    };

    const onInstalled = () => {
      setInstalled(true);
      setInstallPrompt(null);
      setMessage("ติดตั้งแล้ว");
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    window.addEventListener("appinstalled", onInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const install = async () => {
    if (!installPrompt) {
      setMessage("Chrome: กดเมนูมุมขวาบน แล้วเลือก Install app หรือ Add to Home screen");
      return;
    }

    await installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    setInstallPrompt(null);
    setMessage(choice.outcome === "accepted" ? "กำลังติดตั้งแอพ" : "ยังไม่ติดตั้ง");
  };

  return (
    <aside className="pwa-install" aria-live="polite">
      <div>
        <strong>MyPOS QR App</strong>
        <span>{message}</span>
      </div>
      <button type="button" onClick={install} disabled={installed}>
        {installed ? "Installed" : "Install"}
      </button>
    </aside>
  );
}
