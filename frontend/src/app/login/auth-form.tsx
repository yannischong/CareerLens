"use client";

import {
  FormEvent,
  useState,
} from "react";

import { useFormStatus } from "react-dom";

import {
  login,
  signup,
} from "./actions";


type AuthMode =
  | "login"
  | "signup";


type AuthFormProps = {
  serverError?: string;
};


function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent"
    />
  );
}


function SubmitButton({
  mode,
}: {
  mode: AuthMode;
}) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending && <Spinner />}

      {pending
        ? mode === "login"
          ? "Signing in..."
          : "Creating account..."
        : mode === "login"
          ? "Sign in"
          : "Create account"}
    </button>
  );
}


export default function AuthForm({
  serverError,
}: AuthFormProps) {
  const [mode, setMode] =
    useState<AuthMode>("login");

  const [clientError, setClientError] =
    useState<string | null>(null);


  function changeMode(
    nextMode: AuthMode,
  ) {
    setMode(nextMode);
    setClientError(null);
  }


  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    setClientError(null);

    if (mode !== "signup") {
      return;
    }

    const formData =
      new FormData(event.currentTarget);

    const password =
      formData.get("password");

    const confirmPassword =
      formData.get("confirmPassword");

    if (
      typeof password === "string" &&
      typeof confirmPassword === "string" &&
      password !== confirmPassword
    ) {
      event.preventDefault();

      setClientError(
        "Passwords do not match."
      );
    }
  }


  const displayedError =
    clientError || serverError;


  return (
    <div className="rounded-2xl border border-white/20 bg-white p-8 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-6 grid grid-cols-2 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
        <button
          type="button"
          onClick={() =>
            changeMode("login")
          }
          className={`rounded-md px-3 py-2 text-sm font-medium transition ${
            mode === "login"
              ? "bg-white text-blue-700 shadow-sm dark:bg-slate-700 dark:text-blue-300"
              : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
          }`}
        >
          Sign in
        </button>

        <button
          type="button"
          onClick={() =>
            changeMode("signup")
          }
          className={`rounded-md px-3 py-2 text-sm font-medium transition ${
            mode === "signup"
              ? "bg-white text-blue-700 shadow-sm dark:bg-slate-700 dark:text-blue-300"
              : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
          }`}
        >
          Create account
        </button>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-950 dark:text-white">
          {mode === "login"
            ? "Welcome back"
            : "Create your account"}
        </h2>

        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          {mode === "login"
            ? "Sign in to continue to your CareerCompass workspace."
            : "Create an account to start building your CareerCompass workspace."}
        </p>
      </div>

      {displayedError && (
        <div
          role="alert"
          className="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300"
        >
          {displayedError}
        </div>
      )}

      <form
        action={
          mode === "login"
            ? login
            : signup
        }
        onSubmit={handleSubmit}
        className="space-y-4"
      >
        <div>
          <label
            htmlFor="email"
            className="mb-1.5 block text-sm font-medium text-slate-800 dark:text-slate-200"
          >
            Email
          </label>

          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="mb-1.5 block text-sm font-medium text-slate-800 dark:text-slate-200"
          >
            Password
          </label>

          <input
            id="password"
            name="password"
            type="password"
            autoComplete={
              mode === "login"
                ? "current-password"
                : "new-password"
            }
            required
            minLength={8}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
            placeholder="At least 8 characters"
          />
        </div>

        {mode === "signup" && (
          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-1.5 block text-sm font-medium text-slate-800 dark:text-slate-200"
            >
              Confirm password
            </label>

            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
              placeholder="Re-enter your password"
            />
          </div>
        )}

        <SubmitButton mode={mode} />
      </form>

      <p className="mt-5 text-center text-xs text-slate-500 dark:text-slate-400">
        {mode === "login"
          ? "Use the account you created for CareerCompass."
          : "Your password must contain at least 8 characters."}
      </p>
    </div>
  );
}