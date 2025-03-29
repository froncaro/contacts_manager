import os
import csv
import vobject

def parse_vcf(input_file):
    """
    Parses a .vcf file and extracts contact information.

    Args:
        input_file (str): Path to the .vcf file.

    Returns:
        list[dict]: A list of contacts as dictionaries with keys 'Name', 'Email', and 'Phone'.
    """
    contacts = []
    with open(input_file, "r", encoding="utf-8") as vcf_file:
        for vcard in vobject.readComponents(vcf_file):
            contact = {
                "Name": vcard.fn.value if hasattr(vcard, "fn") else "",
                "Email": vcard.email.value if hasattr(vcard, "email") else "",
                "Phone": vcard.tel.value if hasattr(vcard, "tel") else "",
            }
            contacts.append(contact)
    return contacts

def normalize_phone(phone):
    """
    Normalizes phone numbers by replacing '00' with '+'.

    Args:
        phone (str): The phone number to normalize.

    Returns:
        str: The normalized phone number.
    """
    return phone.strip().replace(" ", "").replace("00", "+", 1)

def contact_in_list(contact, contact_list):
    """
    Checks if a contact is already in a list based on Name, Email, and Phone.

    Args:
        contact (dict): The contact to check.
        contact_list (list): The list of contacts to check against.

    Returns:
        bool: True if the contact is in the list, False otherwise.
    """
    return any(
        c["Name"] == contact["Name"] and c["Email"] == contact["Email"] and c["Phone"] == contact["Phone"]
        for c in contact_list
    )

def write_csv(contacts, output_file):
    """
    Writes a list of contacts to a CSV file.

    Args:
        contacts (list[dict]): The list of contacts to write.
        output_file (str): The path to the output CSV file.
    """
    with open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["Name", "Email", "Phone"])
        writer.writeheader()
        writer.writerows(contacts)

    print(f"Filtered contacts saved to CSV: {output_file}")

def write_vcf(contacts, output_file):
    """
    Writes a list of contacts to a .vcf file.

    Args:
        contacts (list[dict]): The list of contacts to write.
        output_file (str): The path to the output .vcf file.
    """
    with open(output_file, "w", encoding="utf-8") as vcf_file:
        for contact in contacts:
            vcard = vobject.vCard()
            if contact["Name"]:
                vcard.add('fn').value = contact["Name"]
            else:
                vcard.add('fn').value = "Unnamed Contact"  # Fallback for missing names

            if contact["Email"]:
                email = vcard.add('email')
                email.value = contact["Email"]
                email.type_param = "INTERNET"
            if contact["Phone"]:
                tel = vcard.add('tel')
                tel.value = contact["Phone"]
                tel.type_param = "CELL"
            vcf_file.write(vcard.serialize())

    print(f"Filtered contacts saved to VCF: {output_file}")

def filter_contacts(input_file, output_dir):
    """
    Filters contacts based on specific criteria and creates new contact lists.

    Args:
        input_file (str): Path to the input .vcf file containing contacts.
        output_dir (str): Directory to save the filtered contact lists.
    """
    # Parse the .vcf file
    contacts = parse_vcf(input_file)

    # Normalize phone numbers
    for contact in contacts:
        contact["Phone"] = normalize_phone(contact["Phone"])

    # Define output files for each filter
    filters = {
        "Doctors": lambda contact: "doc" in contact["Name"].lower() \
            or "dott" in contact["Name"].lower() or 'medi' in contact["Name"].lower(),
        "Restaurants": lambda contact: "rist" in contact["Name"].lower() or "rest" in contact["Name"].lower(),
        "cern_emails": lambda contact: contact["Email"].endswith("cern.ch"),
        "phone_prefix_41": lambda contact: contact["Phone"].startswith("+41"),
        "phone_prefix_39": lambda contact: contact["Phone"].startswith("+39"),
        "phone_prefix_33": lambda contact: contact["Phone"].startswith("+33"),
    }

    # Track contacts that have already been added to a list
    processed_contacts = []

    # Process and write filtered contacts
    for label, condition in filters.items():
        filtered_contacts = [
            contact for contact in contacts
            if condition(contact) and not contact_in_list(contact, processed_contacts)
        ]
        processed_contacts.extend(filtered_contacts)  # Mark contacts as processed

        # Write both CSV and VCF files
        csv_file = os.path.join(output_dir, f"{label}.csv")
        vcf_file = os.path.join(output_dir, f"{label}.vcf")
        write_csv(filtered_contacts, csv_file)
        write_vcf(filtered_contacts, vcf_file)

    # Create 'all_others' for contacts that don't match any filter
    remaining_contacts = [contact for contact in contacts if not contact_in_list(contact, processed_contacts)]
    all_others_csv = os.path.join(output_dir, "all_others.csv")
    all_others_vcf = os.path.join(output_dir, "all_others.vcf")
    write_csv(remaining_contacts, all_others_csv)
    write_vcf(remaining_contacts, all_others_vcf)


if __name__ == "__main__":
    input_file = "contacts_export.vcf"  # Replace with your exported .vcf file
    output_dir = "filtered_contacts"   # Directory to save filtered lists

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    filter_contacts(input_file, output_dir)