import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { ProfileListingItem } from "@/lib/types";

export default function CreatorCard({ profile }: { profile: ProfileListingItem }) {
  return (
    <Link href={`/creators/${profile.slug}`} className="group">
      <Card className="h-full transition-shadow group-hover:shadow-md">
        <CardContent className="flex h-full flex-col gap-3 p-5">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted text-lg font-semibold">
            {profile.name.slice(0, 1)}
          </div>
          <div className="flex-1">
            <p className="font-semibold">{profile.name}</p>
            <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{profile.tagline}</p>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary">{profile.primary_category}</Badge>
            {profile.location && (
              <span className="text-xs text-muted-foreground">{profile.location}</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
