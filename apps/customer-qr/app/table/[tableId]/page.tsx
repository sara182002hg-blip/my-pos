import QrOrderClient from "../../qr-order-client";

interface TablePageProps {
  params: Promise<{ tableId: string }>;
}

export default async function TablePage({ params }: TablePageProps) {
  const { tableId } = await params;
  return <QrOrderClient initialTableId={tableId} />;
}
