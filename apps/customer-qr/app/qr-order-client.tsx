"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  MenuItemSummary,
  ModifierSelection,
  OrderTicket,
  PublicTableResponse,
  SupportedLanguage
} from "@mypos/domain";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:4000";
const languageOptions: SupportedLanguage[] = ["th", "en", "zh", "ja"];
const CART_KEY = "mypos_qr_cart";

const uiCopy: Record<
  SupportedLanguage,
  {
    menu: string;
    available: string;
    requestBill: string;
    cart: string;
    yourOrder: string;
    confirmOrder: string;
    liveStatus: string;
    currentOrders: string;
    emptyCart: string;
    noOrders: string;
    customize: string;
    addToCart: string;
    specialNote: string;
    allergens: string;
    language: string;
    notePlaceholder: string;
    allCategories: string;
    outOfStock: string;
    happyHour: string;
    loading: string;
  }
> = {
  th: {
    menu: "เมนู",
    available: "พร้อมสั่งตอนนี้",
    requestBill: "ขอเช็คบิล",
    cart: "ตะกร้า",
    yourOrder: "รายการของคุณ",
    confirmOrder: "ยืนยันออเดอร์",
    liveStatus: "สถานะล่าสุด",
    currentOrders: "ออเดอร์ของโต๊ะนี้",
    emptyCart: "ยังไม่มีรายการในตะกร้า",
    noOrders: "ยังไม่มีออเดอร์สำหรับโต๊ะนี้",
    customize: "เลือกตัวเลือก",
    addToCart: "เพิ่มลงตะกร้า",
    specialNote: "หมายเหตุพิเศษ",
    allergens: "สารก่อภูมิแพ้",
    language: "ภาษา",
    notePlaceholder: "เช่น ไม่ใส่ผัก, เผ็ดน้อย",
    allCategories: "ทั้งหมด",
    outOfStock: "หมดชั่วคราว",
    happyHour: "Happy Hour",
    loading: "กำลังโหลดเมนู…"
  },
  en: {
    menu: "Menu",
    available: "Available now",
    requestBill: "Request Check Bill",
    cart: "Cart",
    yourOrder: "Your order",
    confirmOrder: "Confirm Order",
    liveStatus: "Live Status",
    currentOrders: "Current orders",
    emptyCart: "Your cart is empty",
    noOrders: "No orders for this table yet",
    customize: "Customize",
    addToCart: "Add To Cart",
    specialNote: "Special note",
    allergens: "Allergens",
    language: "Language",
    notePlaceholder: "For example: no vegetables, less spicy",
    allCategories: "All",
    outOfStock: "Out of stock",
    happyHour: "Happy Hour",
    loading: "Loading menu…"
  },
  zh: {
    menu: "菜单",
    available: "当前可点",
    requestBill: "请求结账",
    cart: "购物车",
    yourOrder: "你的订单",
    confirmOrder: "确认下单",
    liveStatus: "实时状态",
    currentOrders: "当前订单",
    emptyCart: "购物车还没有商品",
    noOrders: "这张桌子还没有订单",
    customize: "选择加料",
    addToCart: "加入购物车",
    specialNote: "特殊备注",
    allergens: "过敏原",
    language: "语言",
    notePlaceholder: "例如: 不要蔬菜, 少辣",
    allCategories: "全部",
    outOfStock: "暂时售罄",
    happyHour: "快乐时光",
    loading: "加载菜单中…"
  },
  ja: {
    menu: "メニュー",
    available: "今すぐ注文できます",
    requestBill: "お会計を依頼",
    cart: "カート",
    yourOrder: "ご注文内容",
    confirmOrder: "注文を確定",
    liveStatus: "注文状況",
    currentOrders: "現在のオーダー",
    emptyCart: "カートに商品がありません",
    noOrders: "このテーブルの注文はまだありません",
    customize: "カスタマイズ",
    addToCart: "カートに追加",
    specialNote: "特記事項",
    allergens: "アレルゲン",
    language: "言語",
    notePlaceholder: "例: 野菜抜き, 辛さ控えめ",
    allCategories: "すべて",
    outOfStock: "売り切れ",
    happyHour: "ハッピーアワー",
    loading: "メニュー読み込み中…"
  }
};

interface CartLine {
  id: string;
  item: MenuItemSummary;
  quantity: number;
  note?: string;
  modifiers: ModifierSelection[];
}

interface QrOrderClientProps {
  initialTableId: string;
}

const formatCurrency = (amount: number) => `THB ${amount.toLocaleString("en-US")}`;

const detectLang = (): SupportedLanguage => {
  if (typeof navigator === "undefined") return "th";
  const lang = navigator.language.toLowerCase();
  if (lang.startsWith("th")) return "th";
  if (lang.startsWith("zh")) return "zh";
  if (lang.startsWith("ja")) return "ja";
  return "en";
};

const getMenuText = (item: MenuItemSummary, language: SupportedLanguage) => {
  const translated = item.translations?.[language] ?? item.translations?.en;
  return {
    name: translated?.name ?? item.name,
    category: translated?.category ?? item.category,
    description: translated?.description ?? item.description ?? ""
  };
};

const getUnitPrice = (item: MenuItemSummary, modifiers: ModifierSelection[]) =>
  item.price + modifiers.reduce((sum, modifier) => sum + modifier.extraPrice, 0);

function MenuSkeleton() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
        <div className="menu-card skeleton-card" key={i}>
          <div className="skel skel-name" />
          <div className="skel skel-cat" />
          <div className="skel skel-price" />
        </div>
      ))}
    </>
  );
}

export default function QrOrderClient({ initialTableId }: QrOrderClientProps) {
  const [language, setLanguage] = useState<SupportedLanguage>("th");
  const [menu, setMenu] = useState<MenuItemSummary[]>([]);
  const [orders, setOrders] = useState<OrderTicket[]>([]);
  const [tableLabel, setTableLabel] = useState<string>(initialTableId);
  const [tableStatus, setTableStatus] = useState<string>("AVAILABLE");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [message, setMessage] = useState("Loading table session");
  const [composerItem, setComposerItem] = useState<MenuItemSummary | null>(null);
  const [composerModifiers, setComposerModifiers] = useState<Record<string, string[]>>({});
  const [composerNote, setComposerNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>("__all__");

  const copy = uiCopy[language];

  const cartTotal = useMemo(
    () =>
      cart.reduce(
        (sum, line) => sum + getUnitPrice(line.item, line.modifiers) * line.quantity,
        0
      ),
    [cart]
  );

  const categories = useMemo(() => {
    const seen = new Set<string>();
    for (const item of menu) {
      if (item.category) seen.add(item.category);
    }
    return Array.from(seen);
  }, [menu]);

  const filteredMenu = useMemo(() => {
    if (activeCategory === "__all__") return menu;
    return menu.filter((item) => item.category === activeCategory);
  }, [menu, activeCategory]);

  /* ── localStorage cart persistence ────────────────────── */
  useEffect(() => {
    try {
      const saved = localStorage.getItem(CART_KEY);
      if (saved) setCart(JSON.parse(saved) as CartLine[]);
    } catch {
      /* ignore */
    }
    setLanguage(detectLang());
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
    } catch {
      /* ignore */
    }
  }, [cart]);

  const loadTable = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/public/tables/${initialTableId}`, {
        cache: "no-store"
      });

      if (!response.ok) throw new Error("Table not found");

      const data = (await response.json()) as PublicTableResponse;
      setMenu(data.menu);
      setOrders(data.orders);
      setTableLabel(data.table.label);
      setTableStatus(data.table.status);
      setMessage(`Table ${data.table.label} ready for ordering`);
    } catch {
      setMessage("Could not load table");
    } finally {
      setLoading(false);
    }
  };

  const lockTable = async () => {
    await fetch(`${apiBaseUrl}/api/public/tables/${initialTableId}/lock`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
  };

  const startCustomize = (item: MenuItemSummary) => {
    if (!item.inStock) return;
    const defaults = Object.fromEntries(
      (item.modifierGroups ?? [])
        .filter((group) => group.required && group.options.length > 0)
        .map((group) => [group.name, [group.options[0].label]])
    ) as Record<string, string[]>;
    setComposerItem(item);
    setComposerModifiers(defaults);
    setComposerNote("");
  };

  const toggleModifier = (groupName: string, optionLabel: string, multiSelect: boolean) => {
    setComposerModifiers((current) => {
      const selected = current[groupName] ?? [];
      const exists = selected.includes(optionLabel);
      if (multiSelect) {
        return {
          ...current,
          [groupName]: exists
            ? selected.filter((entry) => entry !== optionLabel)
            : [...selected, optionLabel]
        };
      }
      return { ...current, [groupName]: exists ? [] : [optionLabel] };
    });
  };

  const addConfiguredItem = () => {
    if (!composerItem) return;
    const modifiers = (composerItem.modifierGroups ?? []).flatMap((group) =>
      (composerModifiers[group.name] ?? []).flatMap((selectedOption) => {
        const option = group.options.find((entry) => entry.label === selectedOption);
        if (!option) return [];
        return [{ group: group.name, option: option.label, extraPrice: option.extraPrice }];
      })
    );
    setCart((current) => [
      ...current,
      {
        id: `${composerItem.id}-${Date.now()}-${current.length + 1}`,
        item: composerItem,
        quantity: 1,
        note: composerNote.trim() || undefined,
        modifiers
      }
    ]);
    setComposerItem(null);
    setComposerModifiers({});
    setComposerNote("");
  };

  const updateCartQuantity = (lineId: string, delta: number) => {
    setCart((current) =>
      current
        .map((line) => (line.id === lineId ? { ...line, quantity: line.quantity + delta } : line))
        .filter((line) => line.quantity > 0)
    );
  };

  const removeFromCart = (lineId: string) => {
    setCart((current) => current.filter((line) => line.id !== lineId));
  };

  const submitOrder = async () => {
    if (cart.length === 0) {
      setMessage("Please add at least one item");
      return;
    }
    try {
      await lockTable();
      const response = await fetch(`${apiBaseUrl}/api/public/tables/${initialTableId}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          guestCount: 2,
          customerName: "QR Guest",
          items: cart.map((line) => ({
            menuItemId: line.item.id,
            quantity: line.quantity,
            note: line.note,
            modifiers: line.modifiers
          })),
          specialNote: `QR web order (${language.toUpperCase()})`
        })
      });
      if (!response.ok) throw new Error("Could not place order");
      setCart([]);
      localStorage.removeItem(CART_KEY);
      setMessage("Order sent to kitchen");
      await loadTable();
    } catch {
      setMessage("Could not place order");
    }
  };

  const requestCheckBill = async () => {
    try {
      await fetch(`${apiBaseUrl}/api/public/tables/${initialTableId}/check-bill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestedBy: "QR Guest" })
      });
      setMessage("Check bill requested");
      await loadTable();
    } catch {
      setMessage("Could not request check bill");
    }
  };

  useEffect(() => {
    lockTable().catch(() => undefined);
    loadTable().catch(() => undefined);
  }, [initialTableId]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      loadTable().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(interval);
  }, [initialTableId]);

  return (
    <main className="qr-page">
      <section className="hero-card">
        <div className="hero-top">
          <div>
            <p className="eyebrow">MyPOS QR Ordering</p>
            <h1>Table {tableLabel}</h1>
            <p className="subtitle">สแกนแล้วสั่งได้ทันที ไม่ต้องดาวน์โหลดแอป</p>
            <p className="status-line">
              {tableStatus} · {message}
            </p>
          </div>
          <div className="language-switcher">
            <span>{copy.language}</span>
            <div className="language-pills">
              {languageOptions.map((option) => (
                <button
                  className={option === language ? "active" : ""}
                  key={option}
                  type="button"
                  onClick={() => setLanguage(option)}
                >
                  {option.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">{copy.menu}</p>
            <h2>{copy.available}</h2>
          </div>
          <button type="button" onClick={requestCheckBill}>
            {copy.requestBill}
          </button>
        </div>

        {/* category tabs */}
        {!loading && categories.length > 1 && (
          <div className="category-tabs">
            <button
              className={`cat-tab${activeCategory === "__all__" ? " is-active" : ""}`}
              type="button"
              onClick={() => setActiveCategory("__all__")}
            >
              {copy.allCategories}
              <span className="cat-count">{menu.length}</span>
            </button>
            {categories.map((cat) => {
              const count = menu.filter((item) => item.category === cat).length;
              return (
                <button
                  className={`cat-tab${activeCategory === cat ? " is-active" : ""}`}
                  key={cat}
                  type="button"
                  onClick={() => setActiveCategory(cat)}
                >
                  {cat}
                  <span className="cat-count">{count}</span>
                </button>
              );
            })}
          </div>
        )}

        <div className="menu-grid">
          {loading ? (
            <MenuSkeleton />
          ) : (
            filteredMenu.map((item) => {
              const text = getMenuText(item, language);
              const oos = !item.inStock;
              const happy = Boolean(item.happyHourPrice);

              return (
                <button
                  className={`menu-card${oos ? " is-oos" : ""}`}
                  type="button"
                  key={item.id}
                  onClick={() => startCustomize(item)}
                  disabled={oos}
                >
                  {item.imageUrl ? (
                    <img className="menu-img" src={item.imageUrl} alt={text.name} />
                  ) : null}
                  <strong>{text.name}</strong>
                  <span>{text.category}</span>
                  <div className="price-row">
                    <small>{formatCurrency(item.price)}</small>
                    {happy ? (
                      <em className="happy-badge">
                        {copy.happyHour} {formatCurrency(item.happyHourPrice!)}
                      </em>
                    ) : null}
                  </div>
                  {oos ? <span className="oos-badge">{copy.outOfStock}</span> : null}
                  {text.description ? <p className="card-copy">{text.description}</p> : null}
                  {item.modifierGroups?.length ? (
                    <div className="tag-row">
                      {item.modifierGroups.map((group) => (
                        <em key={group.id}>{group.name}</em>
                      ))}
                    </div>
                  ) : null}
                </button>
              );
            })
          )}
        </div>
      </section>

      <section className="columns">
        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">{copy.customize}</p>
              <h2>
                {composerItem ? getMenuText(composerItem, language).name : "Select a menu item"}
              </h2>
            </div>
          </div>
          {composerItem ? (
            <div className="composer-stack">
              <p className="card-copy">{getMenuText(composerItem, language).description}</p>
              {(composerItem.modifierGroups ?? []).map((group) => (
                <div className="modifier-group" key={group.id}>
                  <strong>
                    {group.name}
                    {group.required ? " *" : ""}
                  </strong>
                  <div className="option-grid">
                    {group.options.map((option) => {
                      const selected = (composerModifiers[group.name] ?? []).includes(
                        option.label
                      );
                      return (
                        <button
                          className={selected ? "modifier-option selected" : "modifier-option"}
                          key={option.id}
                          type="button"
                          onClick={() =>
                            toggleModifier(group.name, option.label, Boolean(group.multiSelect))
                          }
                        >
                          <span>{option.label}</span>
                          <small>
                            {option.extraPrice > 0
                              ? `+${formatCurrency(option.extraPrice)}`
                              : "Included"}
                          </small>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
              <label className="note-field">
                <span>{copy.specialNote}</span>
                <textarea
                  value={composerNote}
                  onChange={(event) => setComposerNote(event.target.value)}
                  placeholder={copy.notePlaceholder}
                />
              </label>
              {composerItem.allergenInfo?.length ? (
                <p className="muted">
                  {copy.allergens}: {composerItem.allergenInfo.join(", ")}
                </p>
              ) : null}
              <button className="primary" type="button" onClick={addConfiguredItem}>
                {copy.addToCart}
              </button>
            </div>
          ) : (
            <p className="muted">
              Tap a menu card to customize modifiers before adding it to cart.
            </p>
          )}
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">{copy.cart}</p>
              <h2>{copy.yourOrder}</h2>
            </div>
            <strong>{formatCurrency(cartTotal)}</strong>
          </div>
          <div className="cart-stack">
            {cart.length === 0 ? <p className="muted">{copy.emptyCart}</p> : null}
            {cart.map((line) => (
              <div className="cart-line" key={line.id}>
                <div className="cart-row">
                  <div>
                    <strong>{getMenuText(line.item, language).name}</strong>
                    <p>{formatCurrency(getUnitPrice(line.item, line.modifiers))} each</p>
                    {line.modifiers.length ? (
                      <div className="tag-row">
                        {line.modifiers.map((modifier) => (
                          <em key={`${line.id}-${modifier.group}-${modifier.option}`}>
                            {modifier.option}
                          </em>
                        ))}
                      </div>
                    ) : null}
                    {line.note ? <p>{line.note}</p> : null}
                  </div>
                  <button type="button" onClick={() => removeFromCart(line.id)}>
                    Remove
                  </button>
                </div>
                <div className="qty-row">
                  <button type="button" onClick={() => updateCartQuantity(line.id, -1)}>
                    -
                  </button>
                  <strong>x{line.quantity}</strong>
                  <button type="button" onClick={() => updateCartQuantity(line.id, 1)}>
                    +
                  </button>
                  <span>
                    {formatCurrency(getUnitPrice(line.item, line.modifiers) * line.quantity)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button className="primary" type="button" onClick={submitOrder}>
            {copy.confirmOrder}
          </button>
        </article>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">{copy.liveStatus}</p>
            <h2>{copy.currentOrders}</h2>
          </div>
        </div>
        <div className="order-stack">
          {orders.length === 0 ? <p className="muted">{copy.noOrders}</p> : null}
          {orders.map((order) => (
            <div className="order-card" key={order.id}>
              <div>
                <strong>{order.status}</strong>
                <p>
                  {order.items.length} items · {order.waiterName}
                </p>
                <div className="tag-row">
                  {order.items.map((item) => (
                    <em key={item.id}>
                      {item.name} x{item.quantity}
                    </em>
                  ))}
                </div>
              </div>
              <small>{formatCurrency(order.totalAmount)}</small>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
