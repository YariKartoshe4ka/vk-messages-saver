var peer_id = PEERID;
var processed = PROCESSED;

var response = API.messages.getHistory({"offset": processed, "count": 200, "peer_id": peer_id});
processed = processed + response.items.length;

var i = 1;

var messages = response.items;
var count = response.count;


while (i < 25 && processed < count) {
    response = API.messages.getHistory({"offset": processed, "count": 200, "peer_id": peer_id});
    messages = messages + response.items;

    processed = processed + response.items.length;
    i = i + 1;
};

return {"count": count, "processed": processed, "messages": messages};