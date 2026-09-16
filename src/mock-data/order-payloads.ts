export interface OrderItem {
  name: string;
  quantity: number;
  price: number;
  sku?: string;
}

export interface CreateOrderPayload {
  client_order_reference?: string;
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  city: string;
  district?: string;
  cod_amount: number;
  notes?: string;
  items: OrderItem[];
}

export const sampleValidUiOrder: CreateOrderPayload = {
  client_order_reference: `ORD-UI-${Date.now()}`,
  customer_name: "Ahmad Al-Otaibi",
  customer_phone: "+972598847044",
  customer_address: "King Fahd Road, Building 45",
  city: "Ramallah",
  district: "Center",
  cod_amount: 150.00,
  notes: "Deployment smoke test - UI order API",
  items: [
    {
      name: "Chatroom Wireless Headset",
      quantity: 1,
      price: 150.00,
      sku: "SKU-CR-001"
    }
  ]
};

export const sampleValidIntegrationOrders: { orders: CreateOrderPayload[] } = {
  orders: [
    {
      client_order_reference: `ORD-INT-1-${Date.now()}`,
      customer_name: "Sarah Salem",
      customer_phone: "+972598847044",
      customer_address: "Main Street, Villa 12",
      city: "Nablus",
      district: "Al-Makhfiya",
      cod_amount: 280.50,
      notes: "Integration add_orders test item 1",
      items: [
        {
          name: "Smart Watch Series 5",
          quantity: 1,
          price: 280.50,
          sku: "SKU-CR-002"
        }
      ]
    },
    {
      client_order_reference: `ORD-INT-2-${Date.now()}`,
      customer_name: "Omar Khaled",
      customer_phone: "0598847044",
      customer_address: "Jericho Road, Apt 4B",
      city: "Hebron",
      district: "Al-Harayek",
      cod_amount: 95.00,
      notes: "Integration add_orders test item 2",
      items: [
        {
          name: "Phone Stand",
          quantity: 2,
          price: 47.50,
          sku: "SKU-CR-003"
        }
      ]
    }
  ]
};
