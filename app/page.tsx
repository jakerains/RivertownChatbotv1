import { CustomerServiceChatbot } from "@/components/customer-service-chatbot";

export default function Home() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-2xl font-bold text-center mb-8">
        Rivertown Ball Company Customer Service
      </h1>
      <CustomerServiceChatbot />
    </main>
  );
} 