type SearchGuidanceProps = {
    remaining: number | null;
    limit: number;
  };


  export function SearchGuidance({
    remaining,
    limit,
  }: SearchGuidanceProps) {
    return (
      <div className="mt-3 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs font-semibold text-amber-200">

        <span>
          * You are limited to two searches for this free account.
        </span>

        <span>
          Results are saved automatically, so you do not need to search again when you return. *
        </span>

        <span className="ml-1 rounded-full border border-amber-300/60 bg-amber-300/15 px-2.5 py-1 font-bold text-amber-100">
          {
            remaining
            ?? limit
          }/{limit} left
        </span>

      </div>
    );
  }
