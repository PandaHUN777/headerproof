vcl 4.1;

backend default {
    .host = "origin";
    .port = "80";
}

sub vcl_recv {
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }
    if (req.http.Cache-Control ~ "(?i)no-cache" || req.http.Pragma ~ "(?i)no-cache") {
        return (pass);
    }
}

sub vcl_hash {
    hash_data(req.url);
    if (req.http.host) {
        hash_data(req.http.host);
    }
    if (req.url ~ "^/safe") {
        hash_data(req.http.X-Forwarded-Host);
    }
    return (lookup);
}

sub vcl_backend_response {
    if (bereq.url ~ "^/(vulnerable|safe)") {
        set beresp.ttl = 120s;
    }
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
