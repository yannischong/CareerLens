"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";


export async function login(formData: FormData) {
  const supabase = await createClient();

  const email = formData.get("email");
  const password = formData.get("password");

  if (
    typeof email !== "string" ||
    typeof password !== "string"
  ) {
    redirect("/login?error=Invalid+login+details");
  }

  const { error } =
    await supabase.auth.signInWithPassword({
      email,
      password,
    });

  if (error) {
    redirect(
      `/login?error=${encodeURIComponent(error.message)}`
    );
  }

  redirect("/dashboard");
}


export async function signup(formData: FormData) {
  const supabase = await createClient();

  const email = formData.get("email");
  const password = formData.get("password");

  if (
    typeof email !== "string" ||
    typeof password !== "string"
  ) {
    redirect("/login?error=Invalid+signup+details");
  }

  if (password.length < 8) {
    redirect(
      "/login?error=Password+must+be+at+least+8+characters"
    );
  }

  const { error } = await supabase.auth.signUp({
    email,
    password,
  });

  if (error) {
    redirect(
      `/login?error=${encodeURIComponent(error.message)}`
    );
  }

  redirect("/dashboard");
}