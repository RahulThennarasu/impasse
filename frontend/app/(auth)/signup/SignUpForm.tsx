"use client";

import { useState } from "react";

export function SignUpForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      return;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        type="text"
        required
        placeholder="Full name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        className="w-full rounded-md border border-[#e0e0e0] bg-white px-4 py-3 text-sm font-medium text-[#1a1a1a] outline-none transition focus:border-[#7fb069] focus:shadow-[0_0_0_3px_rgba(127,176,105,0.16)]"
      />
      <input
        type="email"
        required
        placeholder="Email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        className="w-full rounded-md border border-[#e0e0e0] bg-white px-4 py-3 text-sm font-medium text-[#1a1a1a] outline-none transition focus:border-[#7fb069] focus:shadow-[0_0_0_3px_rgba(127,176,105,0.16)]"
      />
      <input
        type="password"
        required
        placeholder="Password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        className="w-full rounded-md border border-[#e0e0e0] bg-white px-4 py-3 text-sm font-medium text-[#1a1a1a] outline-none transition focus:border-[#7fb069] focus:shadow-[0_0_0_3px_rgba(127,176,105,0.16)]"
      />
      <input
        type="password"
        required
        placeholder="Confirm password"
        value={confirmPassword}
        onChange={(event) => setConfirmPassword(event.target.value)}
        className="w-full rounded-md border border-[#e0e0e0] bg-white px-4 py-3 text-sm font-medium text-[#1a1a1a] outline-none transition focus:border-[#7fb069] focus:shadow-[0_0_0_3px_rgba(127,176,105,0.16)]"
      />
      <button
        type="submit"
        className="w-full rounded-md bg-[#1a1a1a] px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
      >
        Create account
      </button>
    </form>
  );
}
