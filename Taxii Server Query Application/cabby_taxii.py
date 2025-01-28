from cabby import create_client




if __name__ == "__main__":

    domain = input("Please enter the Domain of the Taxii Server: ")
    discovery_path = input("Please enter the Discovery path of the Taxii Server: ")
    api_key = input("Please enter the API Key for authentiation if necessary, leave blank if not: ")
    
    #Create a client for querying a Taxii server
    
    client = create_client(domain, use_https=True, discovery_path=discovery_path)
   
    #Authenticate the Request with the API Key
    if api_key:
        client.set_auth(username=api_key, password="foo")

    
    

    print("\nBelow is a list of sevieces available on the Taxi server:")
    
    services = client.discover_services()
    for service in services:
        print(f"Service Type = {service.type}, address = {service.address}")

    service_url = input("\nPlease enter the URL of the Collections Endpoint to list available collections: ")

    while True:    
        collections = client.get_collections(
            uri=service_url)
        
        print("\nThe available collections are below:")
        for collection in collections:
            print(collection)

        collection_name = input("\nPlease eneter the name of the Collection you would like to retrieve: ")

        content_blocks = client.poll(collection_name=collection_name)


        for block in content_blocks:
            data_str = block.content.decode('utf-8')
            print(data_str)
        
        decision = input("Would you like to see another collection? (enter y or n): ")
        if decision.lower() == "y":
            continue
        else:
            print("Program exiting")
            break


