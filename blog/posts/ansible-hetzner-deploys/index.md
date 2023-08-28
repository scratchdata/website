---
date: 2023-08-28
publishdate: 2023-08-28
title: Zero-Downtime Hetzner Deploys with Ansible
summary: How we do rolling, zero-downtime deploys to Hetzner Cloud
tags: ["Engineering"]
---

Our hosting set up is really simple: a few cloud servers behind a 
load balancer. Our customers send us more than 1,000 requests/second,
and it's important for deploys to have zero downtime. This is how we do it
using Hetzner cloud servers, load balancers, and our Ansible script.

Of course, you can skip all of this and
[read the Ansible playbook](https://github.com/scratchdata/ScratchDB/blob/main/deploy/web.yaml) yourself.

## Deployment Steps

For each server, our deploy has three steps:

1. Set the server's /healthcheck endpoint to "unhealthy"
2. Wait for the loadbalancer to remove the server from the pool
3. Gracefully shutdown and redeploy the server

What follows are code snippets for each of these steps.

### Set the server's /healthcheck to unhealthy

At the start our Ansible deploy, we just upload a file called "unhealthy" to the server.
If that file is present, then the server will return a 500 error on its healthcheck.

``` yaml
- name: Set server status to unhealthy
    copy:
    content: ""
    dest: ./unhealthy
```

And the corresponding Go code. We're using the [Fiber](https://gofiber.io/) 
web framework.

``` go
func HealthCheck(c *fiber.Ctx) error {
    _, err := os.Stat("./unhealthy")

    if !os.IsNotExist(err) {
        return fiber.ErrBadGateway
    }

    return c.SendString("ok")
}
```

## Wait for the load balancer to stop sending traffic

The tricky part was #2 - there is not a straightforward Ansible module
to wait for the load balancer to stop sending traffic to the, node being
deployed. But we figured it out!

This makes use of two Hetzner API endpoints:

1. [Server Metadata](https://docs.hetzner.cloud/#server-metadata). This endpoint runs on the server 
   and returns information about itself: ip address, hostname, etc. In our case, we just wanted the
   `instance-id`, which is Hetzner's unique identifier for a server.
2. [Get Load Balancer](https://docs.hetzner.cloud/#load-balancers-get-a-load-balancer). This returns
   information about a load balancer, including each of its nodes and healthcheck status. We need the
   `instance-id` from step 1 to check the status in step 2.

To get the `instance-id`, we run this Ansible stanza:

``` yaml
- name: Get Hetzner server ID
  uri:
    url: "http://169.254.169.254/hetzner/v1/metadata/instance-id"
    return_content: true
  register: server_id
```

Now, this is the magic to wait for the LB to mark our server as unhealthy.
This is important because we want to make sure we aren't sending any traffic
before we deploy.

``` yaml
- name: Wait for Hetzner to remove node from LB
  uri:
    url: "https://api.hetzner.cloud/v1/load_balancers/{{hetzner_lb_id}}"
    return_content: true
    headers:
      Authorization: "Bearer {{hetzner_api_key}}"
  register: lb_response
  until: >-
      (
      lb_response.json.load_balancer.targets
      | selectattr('server.id', '==', server_id.content | int)
      ).0.health_status.0.status == 'unhealthy'
  retries: 5
  delay: 5
```

I couldn't have gotten this without help from this [StackOverflow](https://stackoverflow.com/a/76988240/3788)
answer. It is tricky, but here is how it works:

1. Fetches the status of the load balancer and stores the JSON API response into `lb_response`
2. Uses [Jinja's selectattr filter](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.selectattr)
   to parse out the status of the specific server being deployed.
3. Checks to see if that status is unhealthy.
4. If this doesn't happen after 5 retries, cancel the deploy

From here, we can safely shut down the server and proceed with our deploy.

## Conclusion

We've been happy with Hetzner's servers, which are the best value options
we can find on the market today. With a little bit of cleverness we're able
to deploy our service, one node at a time, without any interruption in traffic.