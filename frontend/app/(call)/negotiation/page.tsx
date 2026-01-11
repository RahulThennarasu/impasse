import { NegotiationClient } from "./NegotiationClient";
import { NegotiationProvider } from "./NegotiationContext";

export default function NegotiationPage() {
  return (
    <NegotiationProvider>
      <NegotiationClient />
    </NegotiationProvider>
  );
}
